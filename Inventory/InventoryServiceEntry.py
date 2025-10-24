import asyncio
from contextlib import asynccontextmanager
import sys
import os

from Kitchen.KitchenServiceLogic import KitchenServiceLogic

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, status, HTTPException
from .InventoryServiceLogic import InventoryServiceLogic
from .InventoryServiceModel import CheckRecipeForIngredientsRequest, CheckRecipeForIngredientsResponse, ConsumeIngridientsRequest, ConsumeIngridientsResponse, ConsumeRecipeIngridientsRequest, ConsumeRecipeIngridientsResponse, Menu
from Shared.Logging import logger
from Shared.Lifecycle import startup_http_client, startup_redis, shutdown_redis, shutdown_http_client

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("########################################################################")
    logger.info("##             Inventory service starting up...                       ##")
    logger.info("########################################################################")
    
    await startup_http_client()
    await startup_redis()

    yield

    await shutdown_http_client()
    await shutdown_redis()

    logger.info("########################################################################")
    logger.info("##              Inventory service shutting down...                    ##")
    logger.info("########################################################################")

app = FastAPI(title="Kitchen inventory service", lifespan=lifespan)

inventory_service = InventoryServiceLogic()

@app.post("/checkRecipeForIngredients", response_model=CheckRecipeForIngredientsResponse, status_code=status.HTTP_200_OK)
async def check_recipe_for_ingredients(request: CheckRecipeForIngredientsRequest):
    try:

        logger.info("check_recipe_for_ingredients called", user_id=request.user_id, recipe_ids=request.recipe_ids)

        results = [await inventory_service.checkRecipeForIngridients(task) for task in request.recipe_ids]

        logger.info("check_recipe_for_ingredients results", user_id=request.user_id, results=results)

        return CheckRecipeForIngredientsResponse(user_id=request.user_id, results=results)
    except Exception as e:
        logger.error("Error in check_recipe_for_ingredients", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))
    
@app.post("/consumeRecipeIngridients", response_model=ConsumeRecipeIngridientsResponse, status_code=status.HTTP_200_OK)
async def consume_recipe_ingredients(request: ConsumeRecipeIngridientsRequest):
    try:

        logger.info("consume_recipe_ingredients called", user_id=request.user_id, tasks=request.tasks)

        resultList = [await inventory_service.consumeRecipeIngridients(task) for task in request.tasks]

        logger.info("consume_recipe_ingredients results", user_id=request.user_id, results=resultList)

        return ConsumeRecipeIngridientsResponse(user_id=request.user_id, results=resultList)
    except Exception as e:
        logger.error("Error in consume_recipe_ingredients", error=str(e))
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/menu", response_model=Menu, status_code=status.HTTP_200_OK)
async def get_menu_items():

    logger.info("get_menu_items called")

    menu_items = await inventory_service.get_menu_items()

    logger.info("get_menu_items results", menu_items=menu_items)

    return menu_items

@app.post("/admin/clear-menu-cache")
async def clear_menu_cache():
    from Shared.RedisService import redis_service
    await redis_service.client.delete(redis_service.MENU_CACHE_KEY)
    logger.info(f"{redis_service.MENU_CACHE_KEY} has been cleared.")
    return {"status" : "success"}

@app.get("/admin/cache-status", status_code=status.HTTP_200_OK)
async def cache_status():
    from Shared.RedisService import redis_service
    
    exists = await redis_service.client.exists(redis_service.MENU_CACHE_KEY)

    if exists:
        ttl = await redis_service.client.ttl(redis_service.MENU_CACHE_KEY)
        cached_data = await redis_service.client.get(redis_service.MENU_CACHE_KEY)

        return {
            "exists": True,
            "ttl": ttl,
            "cached_data": cached_data
        }
    else:

        logger.info("Menu cache does not exist.")
        return {
            "exists": False
        }
    


        