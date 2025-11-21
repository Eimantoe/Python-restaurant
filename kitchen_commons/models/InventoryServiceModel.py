from pydantic import BaseModel
from typing import Dict, List

# This model is used to check if a recipe can be made with the available ingredients
class CheckRecipeForIngredientsTask(BaseModel):
    recipe_name: str
    qty: int

class CheckRecipeForIngredientsRequest(BaseModel):
    recipe_ids: List[CheckRecipeForIngredientsTask]

class CheckRecipeForIngredientsResult(BaseModel):
    recipe_id: str
    can_make: bool

class CheckRecipeForIngredientsResponse(BaseModel):
    results: List[CheckRecipeForIngredientsResult]

# This model is used to consume ingredients from the inventory
class ConsumeIngridientsTask(BaseModel):
    ingridient_name: str
    qty: int

class ConsumeIngridientsRequest(BaseModel):
    tasks: List[ConsumeIngridientsTask]

class ConsumeIngridientsResult(BaseModel):
    ingridient_name: str
    consumed: bool

class ConsumeIngridientsResponse(BaseModel):
    results: List[ConsumeIngridientsResult]

# This model is used to consume ingredients for a recipe
class ConsumeRecipeIngridientsTask(BaseModel):
    recipe_name: str
    qty: int

class ConsumeRecipeIngridientsRequest(BaseModel):
    tasks: List[ConsumeRecipeIngridientsTask]

class ConsumeRecipeIngridientsResult(BaseModel):
    recipe_name: str
    consumed: bool
    comments: str = ""

class ConsumeRecipeIngridientsResponse(BaseModel):
    results: List[ConsumeRecipeIngridientsResult]

class MenuItem(BaseModel):
    name: str
    description: str

class Menu(BaseModel):
    items: list[MenuItem]

class AddSupplyRequest(BaseModel):
    supplies: Dict[str, int]  # Dictionary of supply name to quantity

class AddSupplyResponse(BaseModel):
    results: Dict[str, str]  # Dictionary of supply name to success status
