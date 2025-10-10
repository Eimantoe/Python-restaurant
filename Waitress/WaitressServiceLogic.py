import asyncio
from Shared.Settings import settings
from Shared.Logging import logger
from .WaitressServiceModel import Menu
from Shared.RedisService import redis_service
from Events.Events import OrderCanceled, OrderPlaced, OrderReady
import httpx

class WaitressServiceLogic:

    async def get_menu(self):

        logger.info("Fetching menu items...")

        URL = settings.inventory_service_url + "/menu"
        MAX_RETRY_COUNT = 5
        RETRY_DELAY_SECONDS = 2 # Delay between retries

        for attempt in range(MAX_RETRY_COUNT):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(URL)

                if response.status_code == 200:
                    result = Menu.model_validate(response.json())

                    logger.info("Menu items fetched successfully", menu_items=result)
                    await redis_service.set_menu_cache(result)
                    return  # Exit the function if successful
                else:
                    logger.warning("Failed to fetch menu items", status_code=response.status_code)
            except httpx.RequestError as e:
                logger.error("Request error occurred", error=str(e))

            logger.info("Retrying in %d seconds... (Attempt %d/%d)", RETRY_DELAY_SECONDS, attempt + 1, MAX_RETRY_COUNT)
            await asyncio.sleep(RETRY_DELAY_SECONDS)



    async def place_order(self, orderPlacedEvent: OrderPlaced):
        logger.info("Placing order", order_id=orderPlacedEvent.order_id, table_no=orderPlacedEvent.table_no, items=orderPlacedEvent.items)
        await redis_service.publish_waitress_order_event(orderPlacedEvent) # type: ignore

    async def consume_kitchen_order(self) ->  OrderReady | OrderCanceled | None:
        logger.info("Consuming kitchen order event...")
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

            await redis_service.set_last_kitchen_message_id(message_id)

            return kitchen_event
        else:
            logger.error("No new kitchen order events to consume")
            return None