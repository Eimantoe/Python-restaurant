import os
import sqlite3
from typing import Any, Dict, List

from Shared.config import Settings

class InventoryRepository:

    db_path = "./Inventory/Repository/kitchen.db"
    
    # Get a connection to the SQLite database
    def get_connection(self):
        print(f'{os.getcwd()} @@@@@@@@@@@@@@@@@@@@@@@@')
        return sqlite3.connect(self.db_path)
    
    def get_menu_items(self) -> List[Dict[str, str]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, description FROM recipes")
            
            rows    = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            results = [dict(zip(columns, row)) for row in rows]

            return results

    # Check if all ingredients for a recipe are available in the required quantities
    # Returns True if all ingredients are available, False otherwise
    # recipe_name: Name of the recipe to check
    # qty: Quantity of the recipe to check (default is 1)
    def check_ingridients_for_recipe(self, recipe_name: str, qty: int = 1) -> bool:

        # Check if the recipe exists in the database
        recipe_ingridients = self.get_recipe_ingridients_by_name(recipe_name)

        # If no ingredients are found for the recipe, return False
        if not recipe_ingridients:
            return False

        # Check if all ingredients are available in the required quantities
        # If any ingredient is not available in the required quantity, return False
        for ingridient in recipe_ingridients:
            required_qty = ingridient['RequiredQty']
            required_qty *= qty
            if not self.check_ingridient_availability(ingridient['Name'], required_qty):
                return False

        # If all ingredients are available in required quantities
        return True

    # Get the ingredients for a recipe by its name
    # Returns a list of dictionaries containing the ingredient name and required quantity
    def get_recipe_ingridients_by_name(self, recipe_name: str) -> List[Dict[str, Any]]:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, requiredQty FROM recipeingridient WHERE recipe = ?", (recipe_name,))
            
            rows    = cursor.fetchall()
            columns = [desc[0] for desc in cursor.description]

            results = [dict(zip(columns, row)) for row in rows]

            return results

    # Check if a specific ingredient is available in the required quantity 
    # Returns True if the ingredient is available, False otherwise
    def check_ingridient_availability(self, ingridient_name: str, required_qty: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name, qty FROM supplies WHERE name = ?", (ingridient_name,))
            result = cursor.fetchone()
            if result:
                available_qty = result[1]  # Assuming the second column is the quantity
                return available_qty >= required_qty
            return False
        
    def consume_ingridient(self, ingridient_name: str, qty: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("UPDATE supplies SET qty = qty - ? WHERE name = ?", (qty, ingridient_name))
            if cursor.rowcount > 0:
                conn.commit()
                return True
            return False
        
    def consume_recipe_ingridients(self, recipe_name: str, qty: int) -> bool:
        recipe_ingridients = self.get_recipe_ingridients_by_name(recipe_name)

        if not recipe_ingridients:
            return False

        for ingridient in recipe_ingridients:
            required_qty = ingridient['RequiredQty'] * qty
            if not self.consume_ingridient(ingridient['Name'], required_qty):
                return False

        return True