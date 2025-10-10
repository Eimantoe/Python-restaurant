from pydantic import BaseModel, Field
from typing import List
import uuid

# This model is used to check if a recipe can be made with the available ingredients
class CheckRecipeForIngredientsTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "check_recipe_for_ingredients"
    recipe_name: str
    qty: int

class CheckRecipeForIngredientsRequest(BaseModel):
    user_id: str
    recipe_ids: List[CheckRecipeForIngredientsTask]

class CheckRecipeForIngredientsResult(BaseModel):
    id: str
    recipe_id: str
    can_make: bool

class CheckRecipeForIngredientsResponse(BaseModel):
    user_id: str
    results: List[CheckRecipeForIngredientsResult]


# This model is used to consume ingredients from the inventory
class ConsumeIngridientsTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "consume_ingridients"
    ingridient_name: str
    qty: int

class ConsumeIngridientsRequest(BaseModel):
    user_id: str
    tasks: List[ConsumeIngridientsTask]

class ConsumeIngridientsResult(BaseModel):
    id: str
    ingridient_name: str
    consumed: bool

class ConsumeIngridientsResponse(BaseModel):
    user_id: str
    results: List[ConsumeIngridientsResult]

# This model is used to consume ingredients for a recipe
class ConsumeRecipeIngridientsTask(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = "consume_recipe_ingridients"
    recipe_name: str
    qty: int

class ConsumeRecipeIngridientsRequest(BaseModel):
    user_id: str
    tasks: List[ConsumeRecipeIngridientsTask]

class ConsumeRecipeIngridientsResult(BaseModel):
    id: str
    recipe_name: str
    consumed: bool

class ConsumeRecipeIngridientsResponse(BaseModel):
    user_id: str
    results: List[ConsumeRecipeIngridientsResult]

class MenuItem(BaseModel):
    name: str
    description: str

class Menu(BaseModel):
    items: list[MenuItem]
