import asyncio
import json
import traceback
import redis

from kitchen_commons.events.Events import DeadEvent, OrderCanceled, OrderPlaced, OrderReady
from kitchen_commons.models.InventoryServiceModel import ConsumeRecipeIngridientsRequest, ConsumeRecipeIngridientsResponse, ConsumeRecipeIngridientsResult, ConsumeRecipeIngridientsTask

from kitchen_commons.shared.Correlation import generate_correlation_id, set_correlation_id
from kitchen_commons.shared.RedisService import redis_service
from kitchen_commons.shared.Settings import settings
from kitchen_commons.shared.Logging import logger
from kitchen_commons.shared.APIRequest import APIRequest

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


 
    # while true loop - Consume waitress order events 
    # TODO : Exception handling for the True loop
    async def consume_waitress_order_events(self):
        while True:
            try:
                message_id, message_data = await redis_service.consume_waitress_order_event(self.last_waitress_message_id) or (None, None) 

                # If no order's, why bother?
                if message_id is None or message_data is None:
                    await asyncio.sleep(5)
                    continue

                corr_id = message_data.get('correlation_id')
                if corr_id and corr_id != "":
                    set_correlation_id(corr_id)
                else:
                    # Generate new one if missing
                    set_correlation_id(generate_correlation_id())


                # We've got something here to process
                logger.info("Consumed waitress order event", message_id=message_id, message_data=message_data)

                try:
                    # Process the message based on its type
                    await self.process_message(message_data)
                    # Update the last processed message ID
                    self.last_waitress_message_id = message_id # type: ignore
                    await redis_service.set_last_waitress_message_id(self.last_waitress_message_id)
                except Exception as e:
                    # log the error and handle 3 retries
                    logger.error("Error processing waitress order event", error=str(e))
                    self.handle_processing_failure(message_id, message_data, e)
            
            except redis.ConnectionError as e:
                logger.error("Redis connection error", error=str(e))
                await asyncio.sleep(5)  # Wait before retrying
            except Exception as e:
                logger.error("Error processing waitress order event", error=str(e))
                logger.error(traceback.format_exc())

    # Handle processing failure with retries and DLQ
    async def handle_processing_failure(self, message_id, message_data, error):

        # Increment retry count for a message_id
        retry_count = await redis_service.client.hincrby(f"retry:{message_id}", "count", 1)
        
        if retry_count > 3:
            # Move to DLQ
            await redis_service.publish_error_event(DeadEvent(
                order_id=int(message_data.get('order_id', 0)),
                table_no=int(message_data.get('table_no', 0)),
                comments="Moved to DLQ after exceeding retry limit",
                message_id=message_id,
                original_message=json.dumps(message_data),
                error=str(error)
            ))
            logger.error("Message moved to DLQ", message_id=message_id)
            self.last_waitress_message_id = message_id
            await redis_service.set_last_waitress_message_id(message_id)
        else:
            # Exponential backoff before retrying
            logger.info("Retrying message processing", message_id=message_id, retry_count=retry_count, count=3)
            await asyncio.sleep(2 ** retry_count)  

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

        consumeTasksRequestList = ConsumeRecipeIngridientsRequest(
            user_id="kitchen_service",
            tasks=[]
        )

        for item in event.items:
            for name, qty in item.items():
                consumeTask = ConsumeRecipeIngridientsTask(
                    recipe_name=name,
                    qty=qty
                )
                consumeTasksRequestList.tasks.append(consumeTask)

        # If 0 tasksm, cancel the order
        # TODO: Consider if this is the right approach
        if (consumeTasksRequestList.tasks.__len__() == 0):
            logger.warning("No valid items in order", order_id=event.order_id)

            orderCanceled = OrderCanceled(
                order_id=event.order_id,
                table_no=event.table_no,
                comments="CANCELED: No valid items in order"
            )

            logger.info("Publishing order canceled event", order_id=event.order_id)
            await redis_service.publish_kitchen_order_event(orderCanceled.to_redis()) # type: ignore
            return

        if settings.use_grpc:
            result = await self._consume_recipe_ingredients_rpc(consumeTasksRequestList)
        else:
            result = await self._consume_recipe_ingredients(consumeTasksRequestList)

        order_consumption_comments = [f"{consumptionResult.recipe_name}: {'Success' if consumptionResult.consumed else 'Failed'} - {consumptionResult.comments}" for consumptionResult in result.results]

        logger.info("Order ingredient consumption results", order_id=event.order_id, results=order_consumption_comments)

        orderReady = OrderReady(
            order_id = event.order_id,
            table_no = event.table_no,
            comments = ", ".join(order_consumption_comments)
        )

        await redis_service.publish_kitchen_order_event(orderReady) # type: ignore

    # TODO: Implement order canceled handling logic
    async def handle_order_canceled(self, event: OrderCanceled):
        logger.info("Processing order canceled event", order_id=event.order_id, table_no=event.table_no)

    # Call Inventory Service to consume recipe ingredients
    async def _consume_recipe_ingredients(self, request: ConsumeRecipeIngridientsRequest) -> ConsumeRecipeIngridientsResponse:

        logger.info("CONSUME_RECIPE_INGREDIENTS called", user_id=request.user_id, tasks=len(request.tasks))

        api_request = APIRequest(APIRequest.Method.POST, settings.consumeRecipeIngridients_endpoint, request.model_dump())
        response = await api_request.sendRequest()

        if response:
            result = ConsumeRecipeIngridientsResponse.model_validate(response.json())
            logger.info("/consumeRecipeIngridients result", user_id=request.user_id, tasks=len(request.tasks), result=result)
        else:
            logger.error("/consumeRecipeIngridients failed after retries", user_id=request.user_id, tasks=len(request.tasks))
            raise Exception("Failed to consume recipe ingredients from Inventory Service")
        
        return result        

    async def _consume_recipe_ingredients_rpc(self, request: ConsumeRecipeIngridientsRequest) -> ConsumeRecipeIngridientsResponse:
        logger.info("CONSUME_RECIPE_INGREDIENTS_RPC called", number_of_tasks=len(request.tasks), tasks = request.tasks)

        from inventory_service.gRPC.InventoryServicer import InventoryServicer
        from kitchen_commons.proto.generated.inventoryservice_pb2 import ConsumeRecipeIngredientsRequest, ConsumeRecipeIngredientsResponse

        # convert model request to proto request
        protoTaskList = []

        for task in request.tasks:
            protoTask = ConsumeRecipeIngredientsRequest.ConsumeRecipeIngredientsTask(
                recipe_name=task.recipe_name,
                qty=task.qty
            )
            protoTaskList.append(protoTask)
            
        protoRequest = ConsumeRecipeIngredientsRequest(
            ConsumeRecipeIngredientsTasks=protoTaskList
        )

        inventoryServicer = InventoryServicer()
        consumeRecipeIngredientsResponse = inventoryServicer.ConsumeRecipeIngredients(protoRequest)

        consumeRecipeIngredientsResponseModel = ConsumeRecipeIngridientsResponse()
        consumeRecipeIngredientsResponseModel.results = [ConsumeRecipeIngridientsResult(recipe_name=result.recipe_name, consumed=result.consumed, comments=result.comments) for result in consumeRecipeIngredientsResponse.ConsumeRecipeIngredientsResults] 

        logger.info("/consumeRecipeIngridients RPC result", number_of_tasks = len(request.tasks), result=consumeRecipeIngredientsResponseModel)

        return consumeRecipeIngredientsResponseModel