""" kitchen commons - shared models and utilities for kitchen related services """

__version__ = "0.1.0"

from kitchen_commons.events.Events import (
    DeadEvent,
    OrderCanceled,
    OrderPlaced,
    OrderReady
)

from kitchen_commons.models.InventoryServiceModel import (
    CheckRecipeForIngredientsTask,
    CheckRecipeForIngredientsRequest,
    CheckRecipeForIngredientsResult,
    CheckRecipeForIngredientsResponse,
    ConsumeIngridientsTask,
    ConsumeIngridientsRequest,
    ConsumeIngridientsResult,
    ConsumeIngridientsResponse,
    ConsumeRecipeIngridientsTask,
    ConsumeRecipeIngridientsRequest,
    ConsumeRecipeIngridientsResult,
    ConsumeRecipeIngridientsResponse,
    MenuItem,
    Menu
)

from kitchen_commons.models.WaitressServiceModel import (
    MenuItem,
    Menu,
    PlaceOrderRequestItem,
    PlaceOrderRequest,
    PlaceOrderResponse,
    KitchenOrderResponse
)

from kitchen_commons.shared.APIRequest import APIRequest
from kitchen_commons.shared.HTTPClientManager import http_client_manager
from kitchen_commons.shared.Settings import settings
from kitchen_commons.shared.Logging import logger
from kitchen_commons.shared.RedisService import redis_service
from kitchen_commons.shared.Lifecycle import (
    startup_http_client,
    shutdown_http_client,
    startup_redis,
    shutdown_redis
)

__all__ = [
    "__version__"
    "DeadEvent",
    "OrderCanceled",
    "OrderPlaced",
    "OrderReady",
    "CheckRecipeForIngredientsTask",
    "CheckRecipeForIngredientsRequest",
    "CheckRecipeForIngredientsResult",
    "CheckRecipeForIngredientsResponse",
    "ConsumeIngridientsTask",
    "ConsumeIngridientsRequest",
    "ConsumeIngridientsResult",
    "ConsumeIngridientsResponse",
    "ConsumeRecipeIngridientsTask",
    "ConsumeRecipeIngridientsRequest",
    "ConsumeRecipeIngridientsResult",
    "ConsumeRecipeIngridientsResponse",
    "MenuItem",
    "Menu",
    "PlaceOrderRequestItem",
    "PlaceOrderRequest",
    "PlaceOrderResponse",
    "KitchenOrderResponse",
    "APIRequest",
    "http_client_manager",
    "settings",
    "logger",
    "redis_service",
    "startup_http_client",
    "shutdown_http_client",
    "startup_redis",
    "shutdown_redis"
]
