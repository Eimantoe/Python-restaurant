from Shared.config import Settings

from pydantic import BaseModel

class MenuItem(BaseModel):
    name: str
    description: str

class Menu(BaseModel):
    items: list[MenuItem] = []
