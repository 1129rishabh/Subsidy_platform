import psycopg2
from psycopg2 import pool
import logging
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

class DatabaseManager:
    _connection_pool = None

    @classmethod
    def initialize_pool(cls):
        try:
            cls._connection_pool = pool.SimpleConnectionPool(
                1, 20,
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
            logging.info("Database connection pool initialized successfully")
        except Exception as e:
            logging.error(f"Error initializing database connection pool: {e}")
            raise

    @classmethod
    def get_connection(cls):
        if cls._connection_pool is None:
            cls.initialize_pool()
        return cls._connection_pool.getconn()

    @classmethod
    def release_connection(cls, connection):
        cls._connection_pool.putconn(connection)

    @classmethod
    def execute_query(cls, query, params=None):
        connection = None
        cursor = None
        try:
            connection = cls.get_connection()
            cursor = connection.cursor()
            cursor.execute(query, params)
            connection.commit()
            if cursor.description:
                columns = [desc[0] for desc in cursor.description]
                result = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return result
            return None
        except Exception as e:
            if connection:
                connection.rollback()
            logging.error(f"Database query error: {e}")
            raise
        finally:
            if cursor:
                cursor.close()
            if connection:
                cls.release_connection(connection)

    @classmethod
    def close_all_connections(cls):
        if cls._connection_pool:
            cls._connection_pool.closeall()
            logging.info("All database connections closed")
