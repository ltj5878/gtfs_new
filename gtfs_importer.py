#!/usr/bin/env python3
"""
GTFS Data Importer for PostgreSQL

This tool imports GTFS (General Transit Feed Specification) data from ZIP files
or directories into a PostgreSQL database.

Usage:
    python gtfs_importer.py --zip path/to/gtfs.zip
    python gtfs_importer.py --dir path/to/gtfs_folder
    python gtfs_importer.py --zip gtfs.zip --clean --host localhost --database gtfs_db
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
    """Import GTFS data into PostgreSQL database."""

    # Define the order of table imports (respecting foreign key constraints)
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

    # Map GTFS txt files to database table names
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
                 password: Optional[str] = None):
        """Initialize the importer with database connection parameters."""
        self.host = host
        self.port = port
        self.database = database
        self.user = user or os.environ.get('USER', 'postgres')
        self.password = password
        self.conn = None
        self.cursor = None

    def connect(self):
        """Connect to the PostgreSQL database."""
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
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            sys.exit(1)

    def disconnect(self):
        """Close database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Database connection closed")

    def clean_tables(self, tables: Optional[List[str]] = None):
        """Truncate specified tables or all tables."""
        try:
            tables_to_clean = tables if tables else list(reversed(self.TABLE_ORDER))

            print("Cleaning tables...")
            for table in tables_to_clean:
                try:
                    self.cursor.execute(sql.SQL("TRUNCATE TABLE {} CASCADE").format(
                        sql.Identifier(table)
                    ))
                    print(f"  Truncated table: {table}")
                except psycopg2.Error as e:
                    print(f"  Warning: Could not truncate {table}: {e}")

            self.conn.commit()
            print("Tables cleaned successfully")
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error cleaning tables: {e}")

    def import_file(self, file_path: Path, table_name: str) -> int:
        """Import a single GTFS txt file into the database."""
        if not file_path.exists():
            print(f"  Skipping {table_name}: file not found")
            return 0

        try:
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                reader = csv.DictReader(f)
                rows = list(reader)

                if not rows:
                    print(f"  Skipping {table_name}: no data")
                    return 0

                # Get column names from the first row
                columns = list(rows[0].keys())

                # Prepare INSERT statement
                insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ()").format(
                    sql.Identifier(table_name),
                    sql.SQL(', ').join(map(sql.Identifier, columns)),
                    sql.SQL(', ').join(sql.Placeholder() * len(columns))
                )

                # Prepare data for batch insert
                data = []
                for row in rows:
                    # Convert empty strings to None for proper NULL handling
                    values = tuple(v if v != '' else None for v in row.values())
                    data.append(values)

                # Execute batch insert
                execute_batch(self.cursor, insert_query, data, page_size=1000)
                self.conn.commit()

                print(f"  Imported {len(rows):,} rows into {table_name}")
                return len(rows)

        except Exception as e:
            self.conn.rollback()
            print(f"  Error importing {table_name}: {e}")
            return 0

    def import_from_directory(self, directory: Path, tables: Optional[List[str]] = None):
        """Import all GTFS files from a directory."""
        print(f"\nImporting GTFS data from: {directory}")

        total_rows = 0
        tables_to_import = tables if tables else self.TABLE_ORDER

        for table in tables_to_import:
            # Find the corresponding file
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
        """Extract and import GTFS data from a ZIP file."""
        print(f"\nExtracting GTFS data from: {zip_path}")

        # Create temporary extraction directory
        extract_dir = zip_path.parent / f"{zip_path.stem}_temp"
        extract_dir.mkdir(exist_ok=True)

        try:
            # Extract ZIP file
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(extract_dir)
            print(f"Extracted to: {extract_dir}")

            # Import from extracted directory
            self.import_from_directory(extract_dir, tables)

        finally:
            # Clean up temporary directory
            import shutil
            if extract_dir.exists():
                shutil.rmtree(extract_dir)
                print(f"\nCleaned up temporary directory: {extract_dir}")

    def verify_import(self):
        """Verify the imported data by showing row counts."""
        print("\n" + "="*60)
        print("Import Verification - Row Counts")
        print("="*60)

        for table in self.TABLE_ORDER:
            try:
                self.cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(
                    sql.Identifier(table)
                ))
                count = self.cursor.fetchone()[0]
                print(f"  {table:25} {count:>10,} rows")
            except psycopg2.Error:
                print(f"  {table:25} {'N/A':>10}")

        print("="*60)


def main():
    """Main entry point for the GTFS importer."""
    parser = argparse.ArgumentParser(
        description='Import GTFS data into PostgreSQL database',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --zip gtfs_data/gtfs_SF.zip
  %(prog)s --dir gtfs_data/gtfs_SF
  %(prog)s --zip gtfs.zip --clean --database gtfs_db
  %(prog)s --zip gtfs.zip --tables routes stops trips
        """
    )

    # Input source (mutually exclusive)
    source_group = parser.add_mutually_exclusive_group(required=True)
    source_group.add_argument('--zip', type=str, help='Path to GTFS ZIP file')
    source_group.add_argument('--dir', type=str, help='Path to GTFS directory')

    # Database connection parameters
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

    # Import options
    parser.add_argument('--clean', action='store_true',
                       help='Clean (truncate) tables before importing')
    parser.add_argument('--tables', nargs='+',
                       help='Specific tables to import (default: all)')
    parser.add_argument('--no-verify', action='store_true',
                       help='Skip verification after import')

    args = parser.parse_args()

    # Create importer instance
    importer = GTFSImporter(
        host=args.host,
        port=args.port,
        database=args.database,
        user=args.user,
        password=args.password
    )

    try:
        # Connect to database
        importer.connect()

        # Clean tables if requested
        if args.clean:
            importer.clean_tables(args.tables)

        # Import data
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

        # Verify import
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
