import asyncio
from typing import Dict
import httpx

from pydantic import BaseModel, ValidationError

from kitchen_commons.models.WaitressServiceModel import Menu, OrderStatusResponse
from kitchen_commons.shared.Settings import settings
from kitchen_commons.shared.Logging import logger
from kitchen_commons.shared.RedisService import redis_service
from kitchen_commons.events.Events import OrderCanceled, OrderPlaced, OrderReady, BaseEvent
from kitchen_commons.shared.APIRequest import APIRequest


class WaitressServiceLogic:

    async def get_menu(self):

        logger.info("Fetching menu items...")
        api_request = APIRequest(APIRequest.Method.GET, settings.inventory_service_menu_endpoint)

        try:
            response = await api_request.sendRequest()
            result = Menu.model_validate(response.json())
            logger.info("Menu items fetched successfully", menu_items=result)
            await redis_service.set_menu_cache(result)
            return  # Exit the function if successful
        except httpx.HTTPError as e:
            logger.error("API request failed permanently", error=str(e))
            raise Exception("Inventory service unavailable") from e

    async def place_order(self, orderPlacedEvent: OrderPlaced):
        logger.info("Waitress is placing an order event", order_id=orderPlacedEvent.order_id, table_no=orderPlacedEvent.table_no, items=orderPlacedEvent.items)
        await redis_service.publish_waitress_order_event(orderPlacedEvent) # type: ignore

    # Waitress is checking on kitchen order events
    async def consume_kitchen_order(self, latest = True) ->  BaseEvent | None:
        logger.info("Consuming kitchen order event...")

        last_kitchen_message_id = "0-0"

        if latest:
            last_kitchen_message_id = await redis_service.get_last_kitchen_message_id()

        message_id, message_data = await redis_service.consume_kitchen_order_event(last_kitchen_message_id) or (None, None)

        if message_id and message_data:
            logger.info("Consumed kitchen order event", message_id=message_id, message_data=message_data)

            match message_data.get('event_type'):
                case 'OrderReady':
                    logger.info("Consuming kitchen's OrderReady event", order_id=message_data.get('order_id'))
                    kitchen_event = OrderReady.model_validate(message_data)
                case 'OrderCanceled':
                    logger.info("Consuming kitchen's OrderCanceled event", order_id=message_data.get('order_id'))
                    kitchen_event = OrderCanceled.model_validate(message_data)
                case default:
                    logger.error("Unknown event type", event_type=message_data.get('event_type'))
                    raise Exception(f"Unknown event type: {message_data.get('event_type')}")    

            # Update the latest processed message ID
            if latest:
                await redis_service.set_last_kitchen_message_id(message_id)

            return kitchen_event
        else:
            logger.error("No new kitchen order events to consume")
            return None
        
    async def isOrderReady(self, order_id: int) -> OrderStatusResponse:
        logger.info("Checking if order is ready in Redis event queue", order_id=order_id)
        
        last_message_id = "0-0"
        description = None
        status = False

        while True:
            try:
                message_id, message_data = await redis_service.consume_kitchen_order_event(last_message_id) or (None, None)

                if message_id is None or message_data is None:
                    description = f"No events found for order {order_id}"
                    break  # No more messages to process

                baseEvent = BaseEvent.model_validate(message_data)

                last_message_id = message_id
            
                status = baseEvent.order_id == order_id
                if status: 
                    break # Found the relevant event
            except ValidationError as e:
                logger.error("Error validating kitchen event", error=str(e))
                break

        if description is None:
            description = f"Order {order_id} is {'ready' if status else 'in progress'}"

        response = OrderStatusResponse(order_id=order_id, is_ready=status, results=description)

        return response