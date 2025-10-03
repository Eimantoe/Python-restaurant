import json

from typing_extensions import Literal
from pydantic import BaseModel
from typing import List, Dict

class BaseEvent(BaseModel):

    order_id: int
    table_no: int

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
    
    @classmethod
    def from_redis(cls  , data: dict) -> 'OrderPlaced':
        if 'items' in data and isinstance(data['items'], str):
            data['items'] = json.loads(data['items'])
        return cls.model_validate(data)

class KitchenBaseEvent(BaseEvent):
    pass

class OrderCanceled(KitchenBaseEvent):
    event_type: Literal['OrderCanceled'] = 'OrderCanceled'

class OrderReady(KitchenBaseEvent):
    event_type: Literal['OrderReady'] = 'OrderReady'
    comments: str = ""
    