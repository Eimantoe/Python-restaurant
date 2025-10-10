import asyncio
import traceback
import redis
from Events.Events import OrderCanceled, OrderPlaced, OrderReady
from Inventory.InventoryServiceModel import ConsumeRecipeIngridientsRequest, ConsumeRecipeIngridientsResponse, ConsumeRecipeIngridientsTask
from Shared.RedisService import redis_service
from Shared.Settings import settings
from Shared.Logging import logger
import httpx


class KitchenServiceLogic:
    
    async def _initialize_last_message_id(self):
        self.last_waitress_message_id = await redis_service.get_last_waitress_message_id()

    # 3. The async factory using @classmethod
    @classmethod
    async def create(cls):
        """
        Asynchronously creates and initializes an instance of KitchenServiceLogic.
        """
        instance = cls()
        await instance._initialize_last_message_id()
        return instance


    async def consume_waitress_order_events(self):
        while True:
            try:
                message_id, message_data = await redis_service.consume_waitress_order_event(self.last_waitress_message_id) or (None, None)
                
                if message_id is None or message_data is None:
                    await asyncio.sleep(5)
                    continue

                logger.info("Consumed waitress order event", message_id=message_id, message_data=message_data)

                self.last_waitress_message_id = message_id # type: ignore
                await self.process_message(message_data)

                await redis_service.set_last_waitress_message_id(self.last_waitress_message_id)
            except redis.ConnectionError as e:
                logger.error("Redis connection error", error=str(e))
            except Exception as e:
                logger.error("Error processing waitress order event", error=str(e))
                logger.error(traceback.format_exc())

    async def process_message(self, message_data):
        match message_data.get('event_type'):
            case 'OrderPlaced':
                await self.handle_order_placed(OrderPlaced.from_redis(message_data))
            case 'OrderCanceled':
                await self.handle_order_canceled(OrderCanceled.model_validate(message_data))
            case default:
                logger.error("Unknown event type", event_type=message_data.get('event_type'))
                raise Exception(f"Unknown event type: {message_data.get('event_type')}")

    async def handle_order_placed(self, event: OrderPlaced):

        logger.info("Processing order placed event", order_id=event.order_id, items=event.items, table_no=event.table_no)

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
            logger.warning("No valid items in order", order_id=event.order_id)

            orderCanceled = OrderCanceled(
                order_id=event.order_id,
                table_no=event.table_no
            )

            logger.info("Publishing order canceled event", order_id=event.order_id)
            await redis_service.publish_kitchen_order_event(orderCanceled.to_redis()) # type: ignore
            return

        result = await self.consume_recipe_ingredients(consumeRequest)
        
        order_consumption_comments = [f"{consumptionResult.recipe_name}: {'Success' if consumptionResult.consumed else 'Failed'}" for consumptionResult in result.results]

        logger.info("Order ingredient consumption results", order_id=event.order_id, results=order_consumption_comments)

        orderReady = OrderReady(
            order_id = event.order_id,
            table_no = event.table_no,
            comments = ", ".join(order_consumption_comments)
        )

        await redis_service.publish_kitchen_order_event(orderReady) # type: ignore

    async def handle_order_canceled(self, event: OrderCanceled):
        logger.info("Processing order canceled event", order_id=event.order_id, table_no=event.table_no)

    async def consume_recipe_ingredients(self, request: ConsumeRecipeIngridientsRequest) -> ConsumeRecipeIngridientsResponse:

        logger.info("consume_recipe_ingredients called", user_id=request.user_id, tasks=len(request.tasks))

        URL = settings.inventory_service_url + "/consumeRecipeIngridients"

        async with httpx.AsyncClient() as client:
            response = await client.post(URL, json=request.model_dump())

        if response.status_code == 200:
            result = ConsumeRecipeIngridientsResponse.model_validate(response.json())

            logger.info("consume_recipe_ingredients result", user_id=request.user_id, tasks=len(request.tasks), result=result)

        else:
            logger.error("Failed to consume ingredients", status_code=response.status_code, response_text=response.text)
            raise Exception(f"Failed to consume ingredients: {response.status_code} - {response.text}")

        return result           