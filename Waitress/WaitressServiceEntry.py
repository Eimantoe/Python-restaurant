

from contextlib import asynccontextmanager
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Waitress.WaitressServiceModel import Menu
from Shared.RedisService import RedisService
from Shared.config import Settings
import time

if Settings.debug_mode:
    print("WaitressServiceEntry loaded")

from fastapi import FastAPI, HTTPException
from Waitress.WaitressServiceLogic import WaitressServiceLogic
from Shared.RedisService import redis_service

#sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
service_logic = WaitressServiceLogic()

@asynccontextmanager
async def lifespan(app: FastAPI):   
    
    if Settings.debug_mode:
        print("Waitress service starting up...")

    await service_logic.get_menu()

    yield

    if Settings.debug_mode:
        print("Waitress service shutting down...")

app = FastAPI(title="Waitress service", lifespan=lifespan)

@app.middleware("http")
async def add_process_time_header(request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

@app.get("/menu", response_model=Menu)
async def show_menu():
    menu_items = redis_service.get_menu_cache()

    if menu_items:
        return menu_items 
    else:
        await service_logic.get_menu()
        menu_items = redis_service.get_menu_cache()
        if menu_items:
            return menu_items
        else:
            return []

@app.post("/place-order")
async def place_order(orders: list[dict[str, int]]):
    if Settings.debug_mode:
        print(f"Received orders: {orders}")

    order_id = await service_logic.place_order(orders)

    return {"order_id": order_id}

@app.post("/consume-kitchen-order")
async def consume_kitchen_order(last_id: str = '0-0'):
    message_id, message_data = await service_logic.consume_kitchen_order(last_id)
    if message_id and message_data:
        return {"message_id": message_id, "message_data": message_data}
    else:
        raise HTTPException(status_code=404, detail="No new kitchen orders")


