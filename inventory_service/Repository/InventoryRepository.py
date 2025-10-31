import aiosqlite
import asyncio
from typing import Any, Dict, List

from fastapi.concurrency import asynccontextmanager
from fastapi import HTTPException as HttpException
from kitchen_commons.shared.Logging import logger
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class InventoryRepository:

    _BASE_DIR = Path(__file__).resolve().parent
    _DB_PATH = os.path.join(_BASE_DIR, 'kitchen.db')
    
    def __init__(self, pool_size: int = 10):
        self._pool : asyncio.Queue[aiosqlite.Connection] = asyncio.Queue(maxsize=pool_size)
        self._pool_size = pool_size
        self._closed = False

    async def initialize_pool(self):

        """Verify database exists and is accessible."""
        if not os.path.exists(self._DB_PATH):
            raise FileNotFoundError(f"Database not found: {self._DB_PATH}")
        
        """Asynchronously initializes the database connection pool."""
        for _ in range(self._pool_size):
            conn = await aiosqlite.connect(self._DB_PATH)
            await self._pool.put(conn)

        logger.info("Database connection pool initialized")

    def get_connection(self):
        """Asynchronously gets a connection to the SQLite database."""
        if not self._pool:
            raise Exception("Database connection pool is not initialized.")
        return self._pool
    
    @asynccontextmanager
    async def get_connection(self) -> aiosqlite.Connection:

        if self._closed:
            raise Exception("Database connection pool is closed.")
        
        try:

            """Asynchronously gets a connection from the pool."""
            conn = await asyncio.wait_for(self._pool.get(), timeout=5.0)
        except TimeoutError:
            raise HttpException(503, "Timeout while waiting for a database connection.")

        try:
            yield conn
        finally:
            if not self._closed:
                await self._pool.put(conn)

    async def close_pool(self):
        """Asynchronously closes the database connection pool."""
        for _ in range(self._pool_size):
            conn = await self._pool.get()
            await conn.close()
            logger.info("Database connection closed")

    async def get_menu_items(self) -> List[Dict[str, str]]:
        """Asynchronously gets all menu items from the recipes table."""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("SELECT name, description FROM recipes") as cursor:
                rows = await cursor.fetchall()

                logger.info("Menu items fetched from database", item_count=len(rows))

                result = [dict(row) for row in rows]

                logger.info("Menu items formatted", result=result)

                return result

    async def check_ingridients_for_recipe(self, recipe_name: str, qty: int = 1) -> bool:
        """Asynchronously checks if all ingredients for a recipe are available."""
        recipe_ingridients = await self.get_recipe_ingridients_by_name(recipe_name)

        if not recipe_ingridients:
            return False

        for ingridient in recipe_ingridients:
            required_qty = ingridient['requiredQty'] * qty
            if not await self.check_ingridient_availability(ingridient['name'], required_qty):
                return False

        return True

    async def get_recipe_ingridients_by_name(self, recipe_name: str) -> List[Dict[str, Any]]:
        """Asynchronously gets the ingredients for a specific recipe by its name."""
        async with self.get_connection() as conn:
            conn.row_factory = aiosqlite.Row
            async with conn.execute("SELECT name, requiredQty FROM recipeingridient WHERE recipe = ?", (recipe_name,)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def check_ingridient_availability(self, ingridient_name: str, required_qty: int) -> bool:
        """Asynchronously checks if a single ingredient is available in the required quantity."""
        async with self.get_connection() as conn:
            async with conn.execute("SELECT qty FROM supplies WHERE name = ?", (ingridient_name,)) as cursor:
                result = await cursor.fetchone()
                if result:
                    return result[0] >= required_qty
                return False

    async def consume_ingridient(self, conn: aiosqlite.Connection, ingridient_name: str, qty: int) -> bool:
        """
        Asynchronously consumes a specified quantity of an ingredient using an existing connection.
        Note: This method does not commit the transaction.
        """
        cursor = await conn.execute("UPDATE supplies SET qty = qty - ? WHERE name = ? AND qty >= ?", (qty, ingridient_name, qty))
        return cursor.rowcount > 0

    async def consume_recipe_ingridients(self, recipe_name: str, qty: int) -> tuple[bool, str]:
        """
        Asynchronously consumes all ingredients for a recipe in a single database transaction.
        If any ingredient consumption fails, the entire transaction is rolled back.
        """

        async with self.get_connection() as conn:
            # Start a transaction
            await conn.execute("BEGIN")

            recipe_ingridients = await self.get_recipe_ingridients_by_name(recipe_name)

            if not recipe_ingridients:
                logger.warning("Recipe not found when trying to consume ingredients", recipe_name=recipe_name)
                return (False, "Recipe not found")

            for ingredient in recipe_ingridients:

                # SELECTING FOR AN UPDATE LOCKS THE TABLE
                cursor = await conn.execute("SELECT qty FROM supplies WHERE name = ?", (ingredient['name'],))
                
                current_qty_row = (await cursor.fetchone())[0]
                required_qty = ingredient['requiredQty'] * qty

                if current_qty_row < required_qty:
                    # Not enough quantity, roll back and return False
                    await conn.rollback()
                    logger.warning("Insufficient ingredient quantity when trying to consume", recipe_name=recipe_name, ingredient=ingredient['name'], required_qty=required_qty, available_qty=current_qty_row)
                    return (False, f"Insufficient quantity for ingredient: {ingredient['name']}")

            for ingredient in recipe_ingridients:
                await self.consume_ingridient(conn, ingredient['name'], required_qty)

            # If all ingredients are consumed successfully, commit the transaction
            await conn.commit()
            return (True, "Ingredients consumed successfully")