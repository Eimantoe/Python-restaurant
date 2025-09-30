import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from InventoryServiceLogic import InventoryServiceLogic
from InventoryServiceModel import CheckRecipeForIngredientsRequest, CheckRecipeForIngredientsResponse, ConsumeIngridientsRequest, ConsumeIngridientsResponse, ConsumeRecipeIngridientsRequest, ConsumeRecipeIngridientsResponse, Menu
from Shared.config import settings

import time

if settings.debug_mode:
    print("InventoryServiceEntry loaded")

#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

app = FastAPI(title="Kitchen inventory service")

inventory_service = InventoryServiceLogic()

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.post("/checkRecipeForIngredients", response_model=CheckRecipeForIngredientsResponse)
async def check_recipe_for_ingredients(request: CheckRecipeForIngredientsRequest):
    try:
            
        results = [inventory_service.checkRecipeForIngridients(task) for task in request.recipe_ids]
        
        if settings.debug_mode:
            print(f"check_recipe_for_ingridients results: {results}")

        return CheckRecipeForIngredientsResponse(user_id=request.user_id, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    

@app.post("/consumeIngridients", response_model=ConsumeIngridientsResponse)
async def consume_ingredients(request: ConsumeIngridientsRequest):
    try:
        results = [inventory_service.consumeIngridients(task) for task in request.tasks]

        if settings.debug_mode: 
            print(f"consume_ingredients results: {results}")

        return ConsumeIngridientsResponse(user_id=request.user_id, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/consumeRecipeIngridients", response_model=ConsumeRecipeIngridientsResponse)
async def consume_recipe_ingredients(request: ConsumeRecipeIngridientsRequest):
    try:
        results = [inventory_service.consumeRecipeIngridients(task) for task in request.tasks]

        if settings.debug_mode: 
            print(f"consume_recipe_ingredients results: {results}")

        return ConsumeRecipeIngridientsResponse(user_id=request.user_id, results=results)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/menu", response_model=Menu)
async def get_menu_items():
    return inventory_service.get_menu_items()
