from typing import Optional
import redis
from Events.Events import BaseEvent
from Waitress.WaitressServiceModel import Menu
from Shared.config import settings

class RedisService:

    MENU_CACHE_KEY              = "menu_items"
    
    DEFAULT_TTL_SECONDS         = 3600  # 1 hour
    
    WAITRESS_ORDER_EVENTS       = "waitress_order_events"
    KITCHEN_ORDER_EVENTS        = "kitchen_order_events"

    KITCHEN_LAST_MESSAGE_ID_KEY   = "kitchen_last_message_id"
    WAITRESS_LAST_MESSAGE_ID_KEY  = "waitress_last_message_id"

    def __init__(self, host='localhost', port=6379, db=0):
        self.client = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def generate_new_id(self, counter_key: str) -> int: 
        return self.client.incr(counter_key) # type: ignore

    def publish_waitress_order_event(self, base_event: BaseEvent):
        self.publish_event(self.WAITRESS_ORDER_EVENTS, base_event)

    def consume_waitress_order_event(self, last_id: str = '0-0'):
        return self.consume_event(self.WAITRESS_ORDER_EVENTS, last_id)

    def publish_kitchen_order_event(self, base_event: BaseEvent):
        self.publish_event(self.KITCHEN_ORDER_EVENTS, base_event)

    def consume_kitchen_order_event(self, last_id: str = '0-0'):
        return self.consume_event(self.KITCHEN_ORDER_EVENTS, last_id)

    def publish_event(self, stream: str, base_event):
        event_data = base_event.to_redis()
        self.client.xadd(stream, event_data) # type: ignore
        if settings.debug_mode:
            print(f"Event added to Redis stream '{stream}': {event_data}")

    def consume_event(self, stream: str, last_id: str = '0-0'):
        messages = self.client.xread({stream: last_id}, count=1, block=0)
        if messages:
            stream, messages_list = messages[0] # type: ignore
            for message_id, message_data in messages_list:
                return message_id, message_data
        else:
            if settings.debug_mode:
                print(f"No new messages in '{stream}' stream")

    def set_menu_cache(self, menu: Menu) -> None:
        self.client.set(self.MENU_CACHE_KEY, menu.model_dump_json(), ex=self.DEFAULT_TTL_SECONDS)
        if settings.debug_mode:
            print(f"Menu items cached under key '{self.MENU_CACHE_KEY}'")

    def get_menu_cache(self) -> Optional[Menu]:
        cached_menu = self.client.get(self.MENU_CACHE_KEY)

        if not cached_menu and settings.debug_mode:
            print(f"Menu items fetched from cache under key '{self.MENU_CACHE_KEY}': None")
            return None
        
        if settings.debug_mode:
            print(f"Menu items fetched from cache under key '{self.MENU_CACHE_KEY}': {cached_menu}")

        try:
            return Menu.model_validate_json(cached_menu) # type: ignore
        except Exception as e:
            if settings.debug_mode:
                print(f"Error validating cached menu data: {e}")
            return None
        
    def get_last_kitchen_message_id(self,) -> str:
        last_id = self.client.get(self.KITCHEN_LAST_MESSAGE_ID_KEY)
        if settings.debug_mode:
            print(f"Retrieved last kitchen message ID '{last_id}'")
        return last_id if last_id else "0-0" # type: ignore

    def set_last_kitchen_message_id(self, last_id: str):
        self.client.set(self.KITCHEN_LAST_MESSAGE_ID_KEY, last_id)
        if settings.debug_mode:
            print(f"Saved last kitchen message ID '{last_id}'")

    def get_last_waitress_message_id(self,) -> str:
        last_id = self.client.get(self.WAITRESS_LAST_MESSAGE_ID_KEY)
        if settings.debug_mode:
            print(f"Retrieved last waitress message ID '{last_id}'")
        return last_id if last_id else "0-0" # type: ignore

    def set_last_waitress_message_id(self, last_id: str):
        self.client.set(self.WAITRESS_LAST_MESSAGE_ID_KEY, last_id)
        if settings.debug_mode:
            print(f"Saved last waitress message ID '{last_id}'")

redis_service = RedisService()