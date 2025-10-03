import asyncio
from fastapi import HTTPException
from Shared.config import settings
from .WaitressServiceModel import Menu
from Shared.RedisService import redis_service
from Events.Events import KitchenBaseEvent, OrderPlaced
import httpx

class WaitressServiceLogic:

    async def get_menu(self):

        if (settings.debug_mode):
            print("Fetching menu items...")

        URL = "http://localhost:8000/menu"
        MAX_RETRY_COUNT = 5
        RETRY_DELAY_SECONDS = 2 # Delay between retries

        for attempt in range(MAX_RETRY_COUNT):
            try:
                async with httpx.AsyncClient() as client:
                    response = await client.get(URL)

                if response.status_code == 200:
                    result = Menu.model_validate(response.json())

                    if settings.debug_mode:
                        print(f"Menu items: {result}")

                    await redis_service.set_menu_cache(result)
                    return  # Exit the function if successful
                else:
                    if settings.debug_mode:
                        print(f"Failed to fetch menu items, status code: {response.status_code}")
            except httpx.RequestError as e:
                if settings.debug_mode:
                    print(f"Request error occurred: {e}")

            if settings.debug_mode:
                print(f"Retrying in {RETRY_DELAY_SECONDS} seconds... (Attempt {attempt + 1}/{MAX_RETRY_COUNT})")
            await asyncio.sleep(RETRY_DELAY_SECONDS)



    async def place_order(self, orderPlacedEvent: OrderPlaced):
        await redis_service.publish_waitress_order_event(orderPlacedEvent) # type: ignore

    async def consume_kitchen_order(self) -> KitchenBaseEvent | None:

        last_kitchen_message_id = await redis_service.get_last_kitchen_message_id()

        message_id, message_data = await redis_service.consume_kitchen_order_event(last_kitchen_message_id) or (None, None)

        if message_id and message_data:
            if settings.debug_mode:
                print(f"Consumed kitchen order event: {message_id}, {message_data}")

            kitchen_base_event = KitchenBaseEvent.model_validate(message_data)

            await redis_service.set_last_kitchen_message_id(message_id)

            return kitchen_base_event
        else:
            if settings.debug_mode:
                print("No new kitchen order events")
            return None