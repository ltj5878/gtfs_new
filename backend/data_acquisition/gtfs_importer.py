#!/usr/bin/env python3
"""
GTFS 数据导入工具 for PostgreSQL

此工具将 GTFS (General Transit Feed Specification) 数据从 ZIP 文件
或目录导入到 PostgreSQL 数据库中。支持多地区数据隔离。

使用方法:
    python gtfs_importer.py --zip path/to/gtfs.zip --region sf
    python gtfs_importer.py --dir path/to/gtfs_folder --region nyc
    python gtfs_importer.py --zip gtfs.zip --clean --region sydney --host localhost --database gtfs_db
"""

import argparse
import csv
import os
import sys
import zipfile
from pathlib import Path
from typing import Optional, List
import psycopg2
from psycopg2 import sql
from psycopg2.extras import execute_batch


class GTFSImporter:
    """将 GTFS 数据导入 PostgreSQL 数据库"""

    # 定义表导入顺序（遵循外键约束）
    TABLE_ORDER = [
        'agency',
        'routes',
        'route_attributes',
        'directions',
        'stops',
        'calendar',
        'calendar_attributes',
        'calendar_dates',
        'shapes',
        'trips',
        'stop_times',
        'rider_categories',
        'fare_attributes',
        'fare_rider_categories',
        'fare_rules',
        'feed_info',
        'attributions'
    ]

    # GTFS txt 文件到数据库表名的映射
    FILE_TO_TABLE = {
        'agency.txt': 'agency',
        'routes.txt': 'routes',
        'route_attributes.txt': 'route_attributes',
        'directions.txt': 'directions',
        'stops.txt': 'stops',
        'calendar.txt': 'calendar',
        'calendar_attributes.txt': 'calendar_attributes',
        'calendar_dates.txt': 'calendar_dates',
        'shapes.txt': 'shapes',
        'trips.txt': 'trips',
        'stop_times.txt': 'stop_times',
        'rider_categories.txt': 'rider_categories',
        'fare_attributes.txt': 'fare_attributes',
        'fare_rider_categories.txt': 'fare_rider_categories',
        'fare_rules.txt': 'fare_rules',
        'feed_info.txt': 'feed_info',
        'attributions.txt': 'attributions'
    }

    def __init__(self, host: str = 'localhost', port: int = 5432,
                 database: str = 'gtfs_db', user: Optional[str] = None,
                 password: Optional[str] = None, region: str = 'sf'):
        """使用数据库连接参数初始化导入器"""
        self.host = host
        self.port = port
        self.database = database
        self.user = user or os.environ.get('USER', 'postgres')
        self.password = password
        self.region = region
        self.conn = None
        self.cursor = None

    def connect(self):
        """连接到 PostgreSQL 数据库"""
        try:
            conn_params = {
                'host': self.host,
                'port': self.port,
                'database': self.database,
                'user': self.user
            }
            if self.password:
                conn_params['password'] = self.password

            self.conn = psycopg2.connect(**conn_params)
            self.cursor = self.conn.cursor()
            print(f"Connected to database '{self.database}' at {self.host}:{self.port}")
            print(f"Region: {self.region}")
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            sys.exit(1)

    def disconnect(self):
        """关闭数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Database connection closed")

    def clean_tables(self, tables: Optional[List[str]] = None):
        """按 region 清空指定表或所有表"""
        try:
            tables_to_clean = tables if tables else list(reversed(self.TABLE_ORDER))

            print(f"Cleaning tables for region '{self.region}'...")
            for table in tables_to_clean:
                try:
                    # 按 region 删除数据，而不是 TRUNCATE 整个表
                    self.cursor.execute(
                        sql.SQL("DELETE FROM {} WHERE region = %s").format(
                            sql.Identifier(table)
                        ),
                        (self.region,)
                    )
                    deleted = self.cursor.rowcount
                    print(f"  Deleted {deleted} rows from {table} (region={self.region})")
                except psycopg2.Error as e:
                    print(f"  Warning: Could not clean {table}: {e}")
                    self.conn.rollback()

            self.conn.commit()
            print("Tables cleaned successfully")
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error cleaning tables: {e}")

    def get_table_columns(self, table_name: str) -> List[str]:
        """查询数据库表的实际列名（排除 region）"""
        self.cursor.execute(
            """SELECT column_name FROM information_schema.columns
               WHERE table_name = %s AND table_schema = 'public' AND column_name != 'region'
               ORDER BY ordinal_position""",
            (table_name,)
        )
        return [row[0] for row in self.cursor.fetchall()]

    def import_file(self, file_path: Path, table_name: str) -> int:
        """将单个 GTFS txt 文件导入数据库，自动添加 region 列，忽略 CSV 中多余的列"""
        if not file_path.exists():
            print(f"  Skipping {table_name}: file not found")
            return 0

        try:
            # 查询表的实际列（不含 region）
            db_columns = self.get_table_columns(table_name)
            if not db_columns:
                print(f"  Skipping {table_name}: table not found in DB")
                return 0

            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                if not rows:
                    print(f"  Skipping {table_name}: no data")
                    return 0

                # 只保留 CSV 中与 DB 列匹配的列
                csv_columns = list(rows[0].keys())
                matched_columns = [c for c in db_columns if c in csv_columns]
                skipped = [c for c in csv_columns if c not in db_columns]
                if skipped:
                    print(f"  Skipping unknown columns in {table_name}: {skipped}")

                insert_columns = ['region'] + matched_columns

                # 准备 INSERT 语句（冲突时跳过，支持多运营机构同 region 导入）
                insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({}) ON CONFLICT DO NOTHING").format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(map(sql.Identifier, insert_columns)),
                    sql.SQL(', ').join(sql.Placeholder() * len(insert_columns))
                )

                # 准备批量插入的数据
                data = []
                for row in rows:
                    values = tuple(
                        [self.region] +
                        [v.strip() if (v := row.get(c)) and v.strip() else None for c in matched_columns]
                    )
                    data.append(values)

                # 执行批量插入
                execute_batch(self.cursor, insert_query, data, page_size=1000)
                self.conn.commit()

                print(f"  Imported {len(rows):,} rows into {table_name} (region={self.region})")
                return len(rows)

        except Exception as e:
            self.conn.rollback()
            print(f"  Error importing {table_name}: {e}")
            return 0

    def import_from_directory(self, directory: Path, tables: Optional[List[str]] = None):
        """从目录导入所有 GTFS 文件"""
        print(f"\nImporting GTFS data from: {directory} (region={self.region})")

        total_rows = 0
        tables_to_import = tables if tables else self.TABLE_ORDER

        for table in tables_to_import:
            # 查找对应的文件
            file_name = None
            for fname, tname in self.FILE_TO_TABLE.items():
                if tname == table:
                    file_name = fname
                    break

            if not file_name:
                continue

            file_path = directory / file_name
            rows = self.import_file(file_path, table)
            total_rows += rows

        print(f"\nTotal rows imported: {total_rows:,}")

    def import_from_zip(self, zip_path: Path, tables: Optional[List[str]] = None):
        """从 ZIP 文件解压并导入 GTFS 数据"""
        print(f"\nExtracting GTFS data from: {zip_path}")

        # 创建临时解压目录
        extract_dir = zip_path.parent / f"{zip_path.stem}_temp"
        extract_dir.mkdir(exist_ok=True)

        try:
            # 解压 ZIP 文件
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print(f"Extracted to: {extract_dir}")

            # 从解压目录导入
            self.import_from_directory(extract_dir, tables)

        finally:
            # 清理临时目录
            import shutil
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
                print(f"\nCleaned up temporary directory: {extract_dir}")

    def verify_import(self):
        """通过显示行数验证导入的数据"""
        print("\n" + "="*60)
        print(f"Import Verification - Row Counts (region={self.region})")
        print("="*60)

        for table in self.TABLE_ORDER:
            try:
                self.cursor.execute(
                    sql.SQL("SELECT COUNT(*) FROM {} WHERE region = %s").format(
                        sql.Identifier(table)
                    ),
                    (self.region,)
                )
                count = self.cursor.fetchone()[0]
                print(f"  {table:25} {count:>10,} rows")
            except psycopg2.Error:
                print(f"  {table:25} {'N/A':>10}")

        print("="*60)


def main():
    """GTFS 导入器的主入口"""
    parser = argparse.ArgumentParser(
        description='Import GTFS data into PostgreSQL database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --zip gtfs_data/gtfs_SF.zip --region sf
  %(prog)s --dir gtfs_data/gtfs_SF --region sf
  %(prog)s --zip gtfs.zip --clean --region nyc --database gtfs_db
  %(prog)s --zip gtfs.zip --region sydney --tables routes stops trips
        """
    )

    # 输入源（互斥）
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument('--zip', type=str, help='Path to GTFS ZIP file')
    source_group.add_argument('--dir', type=str, help='Path to GTFS directory')

    # 地区参数
    parser.add_argument('--region', type=str, default='sf',
                       help='Region identifier (default: sf). Must match regions table.')

    # 数据库连接参数
    parser.add_argument('--host', type=str, default='localhost',
                       help='Database host (default: localhost)')
    parser.add_argument('--port', type=int, default=5432,
                       help='Database port (default: 5432)')
    parser.add_argument('--database', type=str, default='gtfs_db',
                       help='Database name (default: gtfs_db)')
    parser.add_argument('--user', type=str,
                       help='Database user (default: current system user)')
    parser.add_argument('--password', type=str,
                       help='Database password')

    # 导入选项
    parser.add_argument('--clean', action='store_true',
                       help='Clean tables for this region before importing')
    parser.add_argument('--tables', nargs='+',
                       help='Specific tables to import (default: all)')
    parser.add_argument('--no-verify', action='store_true',
                       help='Skip verification after import')

    args = parser.parse_args()

    # 创建导入器实例
    importer = GTFSImporter(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password,
        region=args.region
    )

    try:
        # 连接数据库
        importer.connect()

        # 如果需要，清空表
        if args.clean:
            importer.clean_tables(args.tables)

        # 导入数据
        if args.zip:
            zip_path = Path(args.zip)
            if not zip_path.exists():
                print(f"Error: ZIP file not found: {zip_path}")
                sys.exit(1)
            importer.import_from_zip(zip_path, args.tables)
        else:
            dir_path = Path(args.dir)
            if not dir_path.exists():
                print(f"Error: Directory not found: {dir_path}")
                sys.exit(1)
            importer.import_from_directory(dir_path, args.tables)

        # 验证导入
        if not args.no_verify:
            importer.verify_import()

        print("\nImport completed successfully!")

    except KeyboardInterrupt:
        print("\n\nImport cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nError during import: {e}")
        sys.exit(1)
    finally:
        importer.disconnect()


if __name__ == '__main__':
    main()
