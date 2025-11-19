#!/usr/bin/env python3
"""
数据库连接模块
提供数据库连接池和查询工具函数
"""

import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
from typing import List, Dict, Any, Optional
import os


class Database:
    """数据库连接管理类"""

    _connection_pool = None

    @classmethod
    def initialize(cls,
                   host: str = 'localhost',
                   port: int = 5432,
                   database: str = 'gtfs_db',
                   user: str = None,
                   password: str = None,
                   minconn: int = 1,
                   maxconn: int = 10):
        """初始化数据库连接池"""
        if user is None:
            user = os.getenv('USER', 'postgres')

        try:
            cls._connection_pool = psycopg2.pool.SimpleConnectionPool(
                minconn,
                maxconn,
                host=host,
                port=port,
                database=database,
                user=user,
                password=password
            )
            print(f"数据库连接池初始化成功: {database}@{host}")
        except Exception as e:
            print(f"数据库连接池初始化失败: {e}")
            raise

    @classmethod
    def get_connection(cls):
        """从连接池获取连接"""
        if cls._connection_pool is None:
            cls.initialize()
        return cls._connection_pool.getconn()

    @classmethod
    def return_connection(cls, conn):
        """归还连接到连接池"""
        if cls._connection_pool:
            cls._connection_pool.putconn(conn)

    @classmethod
    def close_all_connections(cls):
        """关闭所有连接"""
        if cls._connection_pool:
            cls._connection_pool.closeall()
            print("所有数据库连接已关闭")


def execute_query(query: str, params: tuple = None) -> List[Dict[str, Any]]:
    """
    执行查询并返回结果

    Args:
        query: SQL 查询语句
        params: 查询参数

    Returns:
        查询结果列表，每行为一个字典
    """
    conn = None
    try:
        conn = Database.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            results = cursor.fetchall()
            return [dict(row) for row in results]
    except Exception as e:
        print(f"查询执行失败: {e}")
        raise
    finally:
        if conn:
            Database.return_connection(conn)


def execute_query_one(query: str, params: tuple = None) -> Optional[Dict[str, Any]]:
    """
    执行查询并返回单条结果

    Args:
        query: SQL 查询语句
        params: 查询参数

    Returns:
        单条查询结果字典，如果没有结果返回 None
    """
    conn = None
    try:
        conn = Database.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return dict(result) if result else None
    except Exception as e:
        print(f"查询执行失败: {e}")
        raise
    finally:
        if conn:
            Database.return_connection(conn)


def execute_count(query: str, params: tuple = None) -> int:
    """
    执行计数查询

    Args:
        query: SQL 查询语句
        params: 查询参数

    Returns:
        计数结果
    """
    conn = None
    try:
        conn = Database.get_connection()
        with conn.cursor() as cursor:
            cursor.execute(query, params)
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        print(f"计数查询执行失败: {e}")
        raise
    finally:
        if conn:
            Database.return_connection(conn)
