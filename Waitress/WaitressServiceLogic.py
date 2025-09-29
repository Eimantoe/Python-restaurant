from fastapi import HTTPException
from Shared.config import Settings
from WaitressServiceModel import Menu
from Shared.RedisService import redis_service
from Events.Events import OrderPlaced
import httpx

if Settings.debug_mode:
    print("WaitressServiceLogic loaded")

class WaitressServiceLogic:

    async def get_menu(self):

        if (Settings.debug_mode):
            print("Fetching menu items...")

        URL = "http://localhost:8000/menu"

        async with httpx.AsyncClient() as client:
            response = await client.post(URL)

        if response.status_code == 200:
            result = Menu.model_validate(response.json())

            if Settings.debug_mode:
                print(f"Menu items: {result}")

            redis_service.set_menu_cache(result)
        else:
            raise HTTPException(status_code=response.status_code, detail="Failed to fetch menu items")
        

    async def place_order(self, orders: list[dict[str, int]]):
        orderPlacedEvent = OrderPlaced(table_no="5", items=orders)
        redis_service.publish_waitress_order_event(orderPlacedEvent) # type: ignore

    async def consume_kitchen_order(self, last_id: str = '0-0'):
        message_id, message_data = redis_service.consume_kitchen_order_event(last_id) or (None, None)
        return message_id, message_data
