import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import time

from contextlib import asynccontextmanager
from .KitchenServiceLogic import KitchenServiceLogic
from Shared.RedisService import redis_service
from fastapi import FastAPI, HTTPException

from Events.Events import OrderPlaced, OrderCanceled, OrderReady
from Shared.config import settings
from Inventory.InventoryServiceModel import ConsumeRecipeIngridientsRequest, ConsumeRecipeIngridientsResponse, ConsumeRecipeIngridientsTask, ConsumeRecipeIngridientsResult

kitchen_service_logic = KitchenServiceLogic()

@asynccontextmanager
async def lifespan(app: FastAPI):

    if settings.debug_mode:
        print("Kitchen service starting up...")

    await kitchen_service_logic.consume_waitress_order_events()

    yield

    if settings.debug_mode:
        print("Kitchen service shutting down...")

app = FastAPI(title="Kitchen service", lifespan=lifespan)

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response