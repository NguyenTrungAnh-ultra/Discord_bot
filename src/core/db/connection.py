import os
import psycopg2
from psycopg2.extras import RealDictCursor
import asyncpg
from dotenv import load_dotenv

# Ensure environment variables are loaded
load_dotenv()

# Database configuration from environment variables
DB_HOST = os.getenv("DB_HOST", "192.168.0.150")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "news_aggregator")
DB_USER = os.getenv("DB_USER", "DISCORDBOT")
DB_PASS = os.getenv("DB_PASS", "sakura")

class Database:
    """Synchronous Database connection helper using psycopg2."""
    
    @staticmethod
    def get_connection():
        """Returns a new synchronous connection."""
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS
        )

    @staticmethod
    def execute_query(query, params=None, fetch=False):
        """Executes a synchronous query."""
        conn = Database.get_connection()
        try:
            with conn.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute(query, params)
                if fetch:
                    return cur.fetchall()
                conn.commit()
        except Exception as e:
            conn.rollback()
            print(f"Database error: {e}")
            raise e
        finally:
            conn.close()

class AsyncDatabase:
    """Asynchronous Database connection helper using asyncpg."""
    _pool = None

    @classmethod
    async def get_pool(cls):
        """Creates and returns an asyncpg connection pool if it doesn't exist."""
        if cls._pool is None:
            cls._pool = await asyncpg.create_pool(
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASS
            )
        return cls._pool

    @classmethod
    async def execute_query(cls, query, *params):
        """Executes an asynchronous query (INSERT, UPDATE, DELETE)."""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.execute(query, *params)

    @classmethod
    async def fetch_query(cls, query, *params):
        """Fetches results from an asynchronous query (SELECT)."""
        pool = await cls.get_pool()
        async with pool.acquire() as conn:
            return await conn.fetch(query, *params)

