import grpc
from kitchen_commons.proto.generated.inventoryservice_pb2_grpc import InventoryServiceServicer
from kitchen_commons.proto.generated import inventoryservice_pb2

from kitchen_commons.models.InventoryServiceModel import ConsumeRecipeIngridientsResult, ConsumeRecipeIngridientsTask

from inventory_service import InventoryServiceLogic

class InventoryServicer(InventoryServiceServicer):

    inventoryServiceLogic = InventoryServiceLogic()

    def CheckRecipeAvailability(self, request, context):
        return super().CheckRecipeAvailability(request, context)
    
    async def ConsumeRecipeIngredients(self, request, context):
        
        try:
            modelTasks = self._convertProtoConsumeRecipeIngredientTasksToModel(request)
            # Call the business logic to consume recipe ingredients
            modelResult = [await self.inventoryServiceLogic.consumeRecipeIngridients(task) for task in modelTasks]
            
            protoResults = self._convertModelConsumeRecipeIngredientResultsToProto(modelResult)

            return protoResults

        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f'Error consuming recipe ingredients: {str(e)}')
            return 
        
    def _convertProtoConsumeRecipeIngredientTasksToModel(self, protoTasks : inventoryservice_pb2.ConsumeRecipeIngredientsRequest) -> ConsumeRecipeIngridientsTask:

        tasks = []

        for protoConsumeRecipeIngredientsTasks in protoTasks.ConsumeRecipeIngredientsTasks:
            task = ConsumeRecipeIngridientsTask(
                recipe_name=protoConsumeRecipeIngredientsTasks.recipe_name,
                qty=protoConsumeRecipeIngredientsTasks.qty
            )
            tasks.append(task)

        return tasks
    
    def _convertModelConsumeRecipeIngredientResultsToProto(self, modelResults: ConsumeRecipeIngridientsResult) -> inventoryservice_pb2.ConsumeRecipeIngredientsResponse:

        protoResults = []

        for modelConsumeRecipeIngredientsResult in modelResults:
            protoResult = inventoryservice_pb2.ConsumeRecipeIngredientsResult(
                recipe_name=modelConsumeRecipeIngredientsResult.recipe_name,
                consumed=modelConsumeRecipeIngredientsResult.consumed,
                comments=modelConsumeRecipeIngredientsResult.comments
            )
            protoResults.append(protoResult)

        return protoResults
