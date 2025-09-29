from Shared.config import Settings

if Settings.debug_mode:
    print("WaitressServiceModel loaded")

from pydantic import BaseModel

class MenuItem(BaseModel):
    name: str
    description: str

class Menu(BaseModel):
    items: list[MenuItem] = []
