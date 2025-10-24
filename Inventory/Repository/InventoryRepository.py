import aiosqlite
from typing import Any, Dict, List
from Shared.Logging import logger
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class InventoryRepository:

    db_path = "Inventory/Repository/kitchen.db"
     
    def get_connection(self):
        """Asynchronously gets a connection to the SQLite database."""
        return aiosqlite.connect(self.db_path)

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
        recipe_ingridients = await self.get_recipe_ingridients_by_name(recipe_name)

        if not recipe_ingridients:
            logger.warning("Recipe not found when trying to consume ingredients", recipe_name=recipe_name)
            return (False, "Recipe not found")

        async with self.get_connection() as conn:
            try:
                # Start a transaction
                await conn.execute("BEGIN")

                for ingridient in recipe_ingridients:
                    required_qty = ingridient['requiredQty'] * qty
                    success = await self.consume_ingridient(conn, ingridient['name'], required_qty)
                    if not success:
                        # If any ingredient fails, roll back and return False
                        await conn.rollback()
                        return (False, "Failed to consume ingredients")

                # If all ingredients are consumed successfully, commit the transaction
                await conn.commit()
                return (True, "Ingredients consumed successfully")
            except Exception:
                # Rollback on any other exception
                await conn.rollback()
                return (False, "Failed to consume ingredients")