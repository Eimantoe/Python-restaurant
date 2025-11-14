from contextlib import asynccontextmanager
from typing import Dict

from kitchen_commons.events.Events import OrderCanceled, OrderPlaced, OrderReady
from kitchen_commons.models.WaitressServiceModel import KitchenOrderResponse, OrderStatusResponse, PlaceOrderRequest, PlaceOrderResponse, Menu
from kitchen_commons.shared.Settings import settings
from kitchen_commons.shared.Logging import logger
from kitchen_commons.shared.Lifecycle import startup_http_client, startup_redis, shutdown_redis, shutdown_http_client
from kitchen_commons.shared.RedisService import redis_service   
#import os
#import sys

#sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, status
from waitress_service.WaitressServiceLogic import WaitressServiceLogic

waitress_service_logic = WaitressServiceLogic()

@asynccontextmanager
async def lifespan(app: FastAPI):   

    logger.info("########################################################################")
    logger.info("##              Waitress service starting up...                       ##")
    logger.info("########################################################################")

    await startup_http_client()
    await startup_redis()

    await waitress_service_logic.get_menu()

    yield

    await shutdown_http_client()
    await shutdown_redis()

    logger.info("########################################################################")
    logger.info("##              Waitress service shutting down...                     ##")
    logger.info("########################################################################")

app = FastAPI(title="Waitress service", lifespan=lifespan)

@app.get("/menu", response_model=Menu, status_code=status.HTTP_200_OK)
async def show_menu():

    logger.info("Menu endpoint called")

    menu_items = await redis_service.get_menu_cache()

    logger.info("Menu items cache retrieved", menu_items=menu_items)

    if menu_items:
        return menu_items
    else:
        await waitress_service_logic.get_menu()
        menu_items = await redis_service.get_menu_cache()

        logger.info("Menu items cache retrieved after fetching from inventory service", menu_items=menu_items)
        
        if menu_items:
            return menu_items
        else:
            return Menu(items=[])

@app.post("/place-order", response_model=PlaceOrderResponse, status_code=status.HTTP_201_CREATED)
async def place_order(orders: PlaceOrderRequest):
    logger.info("Order placed", orders=orders)

    orderPlacedEvent = OrderPlaced(comments=orders.comments, table_no=orders.table_no, order_id= await redis_service.generate_new_id("event_id_counter"), items=[item for item in orders.items])

    await waitress_service_logic.place_order(orderPlacedEvent)

    return PlaceOrderResponse(order_id=orderPlacedEvent.order_id)

@app.get("/consume-kitchen-order", response_model=KitchenOrderResponse, status_code=status.HTTP_200_OK)
async def consume_kitchen_order():

    logger.info("Consuming kitchen order")

    kitchen_base_event = await waitress_service_logic.consume_kitchen_order()

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

@app.get("/order/{order_id}/status", response_model=OrderStatusResponse, status_code=status.HTTP_200_OK)
async def check_if_order_ready(order_id: int) -> OrderStatusResponse:
    logger.info("Checking if order is ready", order_id=order_id)
    response = await waitress_service_logic.isOrderReady(order_id)
    logger.info("Order is ready", isReady = response.is_ready)
    return response

# Basic health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    logger.info("Health check endpoint called")
    return {"status": "OK"}

