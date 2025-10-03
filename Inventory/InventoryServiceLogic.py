from .InventoryServiceModel import CheckRecipeForIngredientsTask, CheckRecipeForIngredientsResult, ConsumeIngridientsTask, ConsumeIngridientsResult, ConsumeRecipeIngridientsTask, ConsumeRecipeIngridientsResult, Menu, MenuItem
from Shared.config import settings
from .Repository.InventoryRepository import InventoryRepository

import asyncio

class InventoryServiceLogic:

    # This class is responsible for the business logic of the inventory service
    # It interacts with the InventoryRepository to check if a recipe can be made with the available ingredients
    # It provides methods to check if a recipe can be made with the available ingredients   
    def __init__(self):
        self.inventory_repository = InventoryRepository()

    # This method checks if a recipe can be made with the available ingredients
    # It takes a CheckRecipeForIngredientsTask as input and returns a CheckRecipeForIngredientsResult
    # If the recipe exists and all ingredients are available in the required quantities, it returns
    # a result indicating that the recipe can be made. Otherwise, it returns a result indicating
    # that the recipe cannot be made.
    async def checkRecipeForIngridients(self, task: CheckRecipeForIngredientsTask) -> CheckRecipeForIngredientsResult:

        if settings.debug_mode:
            print(f"Checking if recipe '{task.recipe_name}' can be made with quantity {task.qty}")

        # Check if the recipe exists in the database
        if not self.inventory_repository.get_recipe_ingridients_by_name(task.recipe_name):
            print(f"Recipe '{task.recipe_name}' not found in the database.")
            return CheckRecipeForIngredientsResult(
                id=task.id,  # Generate a unique ID for the result
                recipe_id=task.recipe_name,  # Use the task ID as the recipe ID
                can_make=False
            )
        
        # Check if all ingredients for the recipe are available in the required quantities
        can_make = self.inventory_repository.check_ingridients_for_recipe(task.recipe_name, task.qty)

        if not can_make:
            
            if settings.debug_mode:
                print(f"Insufficient ingredients for recipe '{task.recipe_name}' with quantity {task.qty}")
            
            return CheckRecipeForIngredientsResult(
                id=task.id,  # Generate a unique ID for the result
                recipe_id=task.recipe_name,  # Use the task ID as the recipe ID
                can_make=False
            )

        if settings.debug_mode:
            print(f"Recipe '{task.recipe_name}' can be made with the available ingredients.")

        # If all checks pass, return a result indicating the recipe can be made
        return CheckRecipeForIngredientsResult(
            id = task.id,  # Generate a unique ID for the result
            recipe_id=task.recipe_name,  # Use the task ID as the recipe ID
            can_make=True
        )  # Assume we can always make the recipe for now

    async def consumeIngridients(self, task: ConsumeIngridientsTask) -> ConsumeIngridientsResult:
        
        if settings.debug_mode:
            print(f"Consuming ingredients for recipe '{task.ingridient_name}' with quantity {task.qty}")

        # Consume ingredients from the inventory
        consumed = self.inventory_repository.consume_ingridient(task.ingridient_name, task.qty)

        return ConsumeIngridientsResult(
            id=task.id,
            ingridient_name=task.ingridient_name,
            consumed=consumed
        )
    
    async def consumeRecipeIngridients(self, task: ConsumeRecipeIngridientsTask) -> ConsumeRecipeIngridientsResult:
        
        if settings.debug_mode:
            print(f"Consuming ingredients for recipe '{task.recipe_name}' with quantity {task.qty}")

        # Consume ingredients for the recipe from the inventory
        consumed = self.inventory_repository.consume_recipe_ingridients(task.recipe_name, task.qty)

        return ConsumeRecipeIngridientsResult(
            id=task.id,
            recipe_name=task.recipe_name,
            consumed=consumed
        )
    
    async def get_menu_items(self) -> Menu:

        menu_result = self.inventory_repository.get_menu_items()

        menu = Menu(items=[MenuItem(name=item.get("Name"), description=item.get("Description")) for item in menu_result]) # type: ignore

        return menu
