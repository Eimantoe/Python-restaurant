from contextlib import asynccontextmanager
from Events.Events import OrderCanceled, OrderPlaced, OrderReady
from .WaitressServiceModel import KitchenOrderResponse, PlaceOrderRequest, PlaceOrderResponse

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Waitress.WaitressServiceModel import Menu
from Shared.Settings import settings
import time

from fastapi import FastAPI, HTTPException
from Waitress.WaitressServiceLogic import WaitressServiceLogic
from Shared.RedisService import redis_service

from Shared.Logging import logger

service_logic = WaitressServiceLogic()

@asynccontextmanager
async def lifespan(app: FastAPI):   
    logger.info("Waitress service starting up...")

    await service_logic.get_menu()

    yield

    logger.info("Waitress service shutting down...")

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

    logger.info("Menu endpoint called")

    menu_items = await redis_service.get_menu_cache()

    logger.info("Menu items cache retrieved", menu_items=menu_items)

    if menu_items:
        return menu_items 
    else:
        await service_logic.get_menu()
        menu_items = await redis_service.get_menu_cache()

        logger.info("Menu items cache retrieved after fetching from inventory service", menu_items=menu_items)
        
        if menu_items:
            return menu_items
        else:
            return Menu(items=[])

@app.post("/place-order", response_model=PlaceOrderResponse)
async def place_order(orders: PlaceOrderRequest):
    logger.info("Order placed", orders=orders)

    orderPlacedEvent = OrderPlaced(comments=orders.comments, table_no=orders.table_no, order_id= await redis_service.generate_new_id("event_id_counter"), items=[item for item in orders.items])

    await service_logic.place_order(orderPlacedEvent)

    return PlaceOrderResponse(order_id=orderPlacedEvent.order_id)

@app.get("/consume-kitchen-order", response_model=KitchenOrderResponse)
async def consume_kitchen_order():

    logger.info("Consuming kitchen order")

    kitchen_base_event = await service_logic.consume_kitchen_order()

    status = ""

    if kitchen_base_event:
        if isinstance(kitchen_base_event, OrderReady):
            logger.info("Order ready", order_id=kitchen_base_event.order_id)
            status = "Ready"
        elif isinstance(kitchen_base_event, OrderCanceled):
            logger.info("Order canceled", order_id=kitchen_base_event.order_id)
            status = "Canceled"
            
        return KitchenOrderResponse(order_id=kitchen_base_event.order_id, status=status, comments=kitchen_base_event.comments)
    else:
        logger.warning("No new kitchen orders to consume")
        raise HTTPException(status_code=404, detail="No new kitchen orders")


