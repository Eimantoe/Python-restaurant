import asyncio
from contextlib import asynccontextmanager
import sys
import os

from Kitchen.KitchenServiceLogic import KitchenServiceLogic

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException
from .InventoryServiceLogic import InventoryServiceLogic
from .InventoryServiceModel import CheckRecipeForIngredientsRequest, CheckRecipeForIngredientsResponse, ConsumeIngridientsRequest, ConsumeIngridientsResponse, ConsumeRecipeIngridientsRequest, ConsumeRecipeIngridientsResponse, Menu
from Shared.Logging import logger

import time

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("Starting inventory service...")
    
    yield

    logger.info("Inventory service shutting down...")

app = FastAPI(title="Kitchen inventory service", lifespan=lifespan)

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

        logger.info("check_recipe_for_ingredients called", user_id=request.user_id, recipe_ids=request.recipe_ids)

        results = [await inventory_service.checkRecipeForIngridients(task) for task in request.recipe_ids]

        logger.info("check_recipe_for_ingredients results", user_id=request.user_id, results=results)

        return CheckRecipeForIngredientsResponse(user_id=request.user_id, results=results)
    except Exception as e:
        logger.error("Error in check_recipe_for_ingredients", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/consumeRecipeIngridients", response_model=ConsumeRecipeIngridientsResponse)
async def consume_recipe_ingredients(request: ConsumeRecipeIngridientsRequest):
    try:

        logger.info("consume_recipe_ingredients called", user_id=request.user_id, tasks=request.tasks)

        resultList = [await inventory_service.consumeRecipeIngridients(task) for task in request.tasks]

        logger.info("consume_recipe_ingredients results", user_id=request.user_id, results=resultList)

        return ConsumeRecipeIngridientsResponse(user_id=request.user_id, results=resultList)
    except Exception as e:
        logger.error("Error in consume_recipe_ingredients", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/menu", response_model=Menu)
async def get_menu_items():

    logger.info("get_menu_items called")

    menu_items = await inventory_service.get_menu_items()

    logger.info("get_menu_items results", menu_items=menu_items)

    return menu_items
