from typing import List
from pydantic import BaseModel

class MenuItem(BaseModel):
    name: str
    description: str

class Menu(BaseModel):
    items: list[MenuItem] = []

class PlaceOrderRequestItem(BaseModel):
    name: str
    qty: int

class PlaceOrderRequest(BaseModel):
    table_no: int
    items: List[PlaceOrderRequestItem]

class PlaceOrderResponse(BaseModel):
    order_id: int

