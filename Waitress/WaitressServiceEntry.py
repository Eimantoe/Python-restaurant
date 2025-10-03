

from contextlib import asynccontextmanager
from Events.Events import OrderCanceled, OrderPlaced, OrderReady
from .WaitressServiceModel import KitchenOrderResponse, PlaceOrderRequest, PlaceOrderRequestItem, PlaceOrderResponse

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Waitress.WaitressServiceModel import Menu
from Shared.config import settings
import time

from fastapi import FastAPI, HTTPException
from Waitress.WaitressServiceLogic import WaitressServiceLogic
from Shared.RedisService import redis_service

service_logic = WaitressServiceLogic()

@asynccontextmanager
async def lifespan(app: FastAPI):   
    
    if settings.debug_mode:
        print("Waitress service starting up...")

    await service_logic.get_menu()

    yield

    if settings.debug_mode:
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
    menu_items = await redis_service.get_menu_cache()

    if menu_items:
        return menu_items 
    else:
        await service_logic.get_menu()
        menu_items = await redis_service.get_menu_cache()
        if menu_items:
            return menu_items
        else:
            return Menu(items=[])

@app.post("/place-order", response_model=PlaceOrderResponse)
async def place_order(orders: PlaceOrderRequest):
    if settings.debug_mode:
        print(f"Received orders: {orders}")

    orderPlacedEvent = OrderPlaced(table_no=orders.table_no, order_id= redis_service.generate_new_id("event_id_counter"), items=[item for item in orders.items])

    await service_logic.place_order(orderPlacedEvent)

    return PlaceOrderResponse(order_id=orderPlacedEvent.order_id)

@app.get("/consume-kitchen-order", response_model=KitchenOrderResponse)
async def consume_kitchen_order():

    kitchen_base_event = await service_logic.consume_kitchen_order()

    if kitchen_base_event:
        if isinstance(kitchen_base_event, OrderReady):
            if settings.debug_mode:
                print(f"Order ready: {kitchen_base_event.order_id}")
            return KitchenOrderResponse(order_id=kitchen_base_event.order_id, status="Ready")
        elif isinstance(kitchen_base_event, OrderCanceled):
            if settings.debug_mode:
                print(f"Order canceled: {kitchen_base_event.order_id}")
            return KitchenOrderResponse(order_id=kitchen_base_event.order_id, status="Canceled")

    else:
        raise HTTPException(status_code=404, detail="No new kitchen orders")


