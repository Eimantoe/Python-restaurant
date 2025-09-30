import asyncio
import redis
from Events.Events import OrderCanceled, OrderPlaced, OrderReady
from Inventory.InventoryServiceModel import ConsumeRecipeIngridientsRequest, ConsumeRecipeIngridientsResponse, ConsumeRecipeIngridientsResult, ConsumeRecipeIngridientsTask
from Shared.RedisService import redis_service
from Shared.config import settings
from time import sleep
import httpx


class KitchenServiceLogic:
    
    def __init__(self):
        self.last_order_id : str = redis_service.get_last_processed_id() or '0-0'

    async def consume_waitress_order_events(self):
        while True:
            try:
                message_id, message_data = redis_service.consume_waitress_order_event(self.last_order_id) or (None, None)
                
                if message_id is None or message_data is None:
                    await asyncio.sleep(100)
                    continue

                self.last_order_id = message_id # type: ignore
                self.process_message(message_data)

                redis_service.set_last_processed_id(self.last_order_id)
            except redis.ConnectionError as e:
                print(f"Redis connection error: {e}")
            except Exception as e:
                print(f"An error occurred: {e}")

    def process_message(self, message_data):
            match message_data.get('event_type'):
                case 'OrderPlaced':
                    self.handle_order_placed(OrderPlaced(**message_data))
                case 'OrderCanceled':
                    self.handle_order_canceled(OrderCanceled(**message_data))

    def handle_order_placed(self, event: OrderPlaced):

        if settings.debug_mode:
            print(f"Order placed: {event.order_id}, Items: {event.items}, Table No: {event.table_no}")

        consumeRequest = ConsumeRecipeIngridientsRequest(
            user_id="kitchen_service",
            tasks=[]
        )

        for item in event.items:
            for name, qty in item.items():
                consumeTask = ConsumeRecipeIngridientsTask(
                    recipe_name=name,
                    qty=qty
                )
                consumeRequest.tasks.append(consumeTask)

        if (consumeRequest.tasks.__len__() == 0):
            if settings.debug_mode:
                print(f"No valid items in order {event.order_id}, canceling order")

            orderCanceled = OrderCanceled(
                order_id=event.order_id,
                table_no=event.table_no
            )

            redis_service.publish_kitchen_order_event(orderCanceled.to_redis()) # type: ignore

            return

        result = self.consume_recipe_ingredients(consumeRequest)

        if settings.debug_mode:
            print(f"All ingredients consumed for order {event.order_id}, order is ready")

        orderReady = OrderReady(
            order_id=event.order_id,
            table_no=event.table_no
        )

        redis_service.publish_kitchen_order_event(orderReady) # type: ignore

    def handle_order_canceled(self, event: OrderCanceled):
        if settings.debug_mode:
            print(f"Order canceled: {event.order_id}")

    async def consume_recipe_ingredients(self, request: ConsumeRecipeIngridientsRequest) -> ConsumeRecipeIngridientsResponse:

        if settings.debug_mode:
            print(f"Consuming ingredients for {request.user_id}, Tasks: {request.tasks}")

        URL = "http://localhost:8000/consumeRecipeIngridients"

        async with httpx.AsyncClient() as client:
            response = await client.post(URL, json=request)

        if response.status_code == 200:
            result = ConsumeRecipeIngridientsResponse.model_validate(response.json())

            if settings.debug_mode:
                print(f"Ingredient consume response: {result}")

        else:

            result = ConsumeRecipeIngridientsResponse(
                user_id="kitchen_service",
                results=[
                    ConsumeRecipeIngridientsResult(
                        id=task.id,
                        recipe_name=task.recipe_name,
                        consumed=False
                    ) for task in request.tasks
                ]
            )

            if settings.debug_mode:
                print(f"Error consuming ingredients: {response.status_code}")

        # Simulate processing time
        await asyncio.sleep(100)

        return result           