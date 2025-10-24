from .InventoryServiceModel import CheckRecipeForIngredientsTask, CheckRecipeForIngredientsResult, ConsumeIngridientsTask, ConsumeIngridientsResult, ConsumeRecipeIngridientsTask, ConsumeRecipeIngridientsResult, Menu, MenuItem
from .Repository.InventoryRepository import InventoryRepository
from Shared.Logging import logger


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

        logger.info("check_recipe_for_ingredients called", recipe_name=task.recipe_name, qty=task.qty)
        
        # Check if the recipe exists in the database
        if not await self.inventory_repository.get_recipe_ingridients_by_name(task.recipe_name):
            
            logger.warning("Recipe not found", recipe_name=task.recipe_name)
            
            return CheckRecipeForIngredientsResult(
                id=task.id,  # Generate a unique ID for the result
                recipe_id=task.recipe_name,  # Use the task ID as the recipe ID
                can_make=False
            )
        
        # Check if all ingredients for the recipe are available in the required quantities
        can_make = await self.inventory_repository.check_ingridients_for_recipe(task.recipe_name, task.qty)

        if not can_make:
            
            logger.warning("Insufficient ingredients for recipe", recipe_name=task.recipe_name, qty=task.qty)

            return CheckRecipeForIngredientsResult(
                id=task.id,  # Generate a unique ID for the result
                recipe_id=task.recipe_name,  # Use the task ID as the recipe ID
                can_make=False
            )

        logger.info("Recipe can be made", recipe_name=task.recipe_name)

        # If all checks pass, return a result indicating the recipe can be made
        return CheckRecipeForIngredientsResult(
            id = task.id,  # Generate a unique ID for the result
            recipe_id=task.recipe_name,  # Use the task ID as the recipe ID
            can_make=True
        )  # Assume we can always make the recipe for now



    async def consumeRecipeIngridients(self, task: ConsumeRecipeIngridientsTask) -> ConsumeRecipeIngridientsResult:
        
        logger.info("consume_recipe_ingredients called", recipe_name=task.recipe_name, qty=task.qty)

        # Consume ingredients for the recipe from the inventory
        (consumed, comments) = await self.inventory_repository.consume_recipe_ingridients(task.recipe_name, task.qty)

        logger.info("consume_recipe_ingredients result", recipe_name=task.recipe_name, qty=task.qty, consumed=consumed)

        return ConsumeRecipeIngridientsResult(
            id=task.id,
            recipe_name=task.recipe_name,
            consumed=consumed,
            comments=comments
        )
    
    async def get_menu_items(self) -> Menu:

        logger.info("get_menu_items called")

        menu_result = await self.inventory_repository.get_menu_items()

        logger.info("get_menu_items result", menu_items=menu_result)

        menu = Menu(items=[MenuItem(name=item.get("name"), description=item.get("description")) for item in menu_result]) # type: ignore

        return menu

