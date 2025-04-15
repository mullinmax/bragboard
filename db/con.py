import os
from typing import Any, Dict, List, Optional, Set

import asyncpg


def get_db_connection_params() -> Dict[str, Any]:
    """Get database connection parameters from environment variables with defaults"""
    return {
        "host": os.getenv("DATABASE_HOST", "localhost"),
        "port": int(os.getenv("DATABASE_PORT", "5432")),
        "user": os.getenv("DATABASE_USER", "postgres"),
        "password": os.getenv("DATABASE_PASSWORD", "postgres"),
        "database": os.getenv("DATABASE_NAME", "bragboard"),
    }


class AsyncDatabase:
    _instance = None
    _initialized_tables: Set[str] = set()
    _default_connection_params = get_db_connection_params()

    def __init__(self, connection_params: Optional[Dict[str, Any]] = None):
        self.connection_params = connection_params or self._default_connection_params
        self.pool = None

    async def initialize_pool(self):
        if not self.pool:
            self.pool = await asyncpg.create_pool(**self.connection_params)

    @classmethod
    async def get_instance(cls, connection_params: Optional[Dict[str, Any]] = None):
        connection_params = connection_params or cls._default_connection_params

        # Create new instance if none exists or if connection params are different
        if cls._instance is None or cls._instance.connection_params != connection_params:
            cls._instance = cls(connection_params)
            await cls._instance.initialize_pool()
        return cls._instance

    async def execute(self, query: str, params: tuple = ()) -> None:
        await self.initialize_pool()
        async with self.pool.acquire() as connection:
            await connection.execute(query, *params)

    async def fetchone(self, query: str, params: tuple = ()) -> Optional[Dict[str, Any]]:
        await self.initialize_pool()
        async with self.pool.acquire() as connection:
            row = await connection.fetchrow(query, *params)
            return dict(row) if row else None

    async def fetchall(self, query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        await self.initialize_pool()
        async with self.pool.acquire() as connection:
            rows = await connection.fetch(query, *params)
            return [dict(row) for row in rows]

    async def table_exists(self, table_name: str) -> bool:
        query = """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = $1
            );
        """
        result = await self.fetchone(query, (table_name,))
        return result and result.get("exists", False)

    @staticmethod
    def is_valid_identifier(name: str) -> bool:
        """Check if a string is a valid SQL identifier name"""
        return name.isalnum() or (name.replace("_", "").isalnum() and not name[0].isdigit())


class BaseModelDB:
    table_name: str = ""
    connection_params: Dict[str, Any] = None  # Will use default from AsyncDatabase
    schema_definition: str = ""

    @classmethod
    async def get_db(cls) -> AsyncDatabase:
        # Singleton DB connection using either custom connection params or defaults
        return await AsyncDatabase.get_instance(cls.connection_params)

    @classmethod
    async def initialize(cls):
        """Initialize the table if it doesn't already exist"""
        db = await cls.get_db()

        # Skip if already initialized
        if cls.table_name in AsyncDatabase._initialized_tables:
            return

        # Create table if it doesn't exist
        if not await db.table_exists(cls.table_name):
            if not cls.schema_definition:
                raise ValueError(f"No schema defined for {cls.__name__}")
            await db.execute(cls.schema_definition)

        # Mark as initialized
        AsyncDatabase._initialized_tables.add(cls.table_name)

    @classmethod
    def validate_column_names(cls, column_names):
        """Validate that column names are safe to use in SQL"""
        for name in column_names:
            if not AsyncDatabase.is_valid_identifier(name):
                raise ValueError(f"Invalid column name: {name}")

    @classmethod
    async def insert(cls, **kwargs):
        await cls.initialize()

        # Safety check for column names
        cls.validate_column_names(kwargs.keys())

        columns = ", ".join(f'"{key}"' for key in kwargs)
        param_indices = ", ".join([f"${i+1}" for i in range(len(kwargs))])
        query = f'INSERT INTO "{cls.table_name}" ({columns}) VALUES ({param_indices})'
        await (await cls.get_db()).execute(query, tuple(kwargs.values()))

    @classmethod
    async def get(cls, **kwargs):
        await cls.initialize()

        # Safety check for column names
        cls.validate_column_names(kwargs.keys())

        if not kwargs:
            raise ValueError("At least one condition is required")

        conditions = " AND ".join([f'"{key}" = ${i+1}' for i, key in enumerate(kwargs)])
        query = f'SELECT * FROM "{cls.table_name}" WHERE {conditions}'
        return await (await cls.get_db()).fetchone(query, tuple(kwargs.values()))

    @classmethod
    async def all(cls):
        await cls.initialize()
        query = f'SELECT * FROM "{cls.table_name}"'
        return await (await cls.get_db()).fetchall(query)

    @classmethod
    async def delete(cls, **kwargs):
        await cls.initialize()

        # Safety check for column names
        cls.validate_column_names(kwargs.keys())

        if not kwargs:
            raise ValueError("At least one condition is required")

        conditions = " AND ".join([f'"{key}" = ${i+1}' for i, key in enumerate(kwargs)])
        query = f'DELETE FROM "{cls.table_name}" WHERE {conditions}'
        await (await cls.get_db()).execute(query, tuple(kwargs.values()))


# Example usage - no need to specify connection params anymore
class User(BaseModelDB):
    table_name = "users"
    schema_definition = """
    CREATE TABLE IF NOT EXISTS "users" (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    )
    """


class Machine(BaseModelDB):
    table_name = "machines"
    schema_definition = """
    CREATE TABLE IF NOT EXISTS "machines" (
        id SERIAL PRIMARY KEY,
        name TEXT NOT NULL,
        last_seen TIMESTAMP NOT NULL
    )
    """


class Game(BaseModelDB):
    table_name = "games"
    schema_definition = """
    CREATE TABLE IF NOT EXISTS "games" (
        id SERIAL PRIMARY KEY,
        date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    )
    """
