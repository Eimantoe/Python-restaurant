import json
from typing_extensions import Literal
from pydantic import BaseModel
from typing import List, Dict
from Shared.RedisService import redis_service

class BaseEvent(BaseModel):

    order_id: int = redis_service.generate_new_id("event_id_counter")
    table_no: str

    def to_redis(self) -> dict[str, str]:
        data = self.model_dump()
        redis_data = {}

        for key, value in data.items():
            if isinstance(value, (list, dict)):
                # 1. Serialize complex types
                redis_data[str(key)] = json.dumps(value)
            elif value is None:
                # Handle None as an empty string
                redis_data[str(key)] = ""
            else:
                # 2. Convert all other simple types
                redis_data[str(key)] = str(value)

        return redis_data

class OrderPlaced(BaseEvent):
    event_type: Literal['OrderPlaced'] = 'OrderPlaced'
    items: List[Dict[str, int]]
    
class OrderCanceled(BaseEvent):
    event_type: Literal['OrderCanceled'] = 'OrderCanceled'

class OrderReady(BaseEvent):
    event_type: Literal['OrderReady'] = 'OrderReady'
    