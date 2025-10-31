from typing import Optional
import redis.asyncio as redis
from kitchen_commons.events.Events import BaseEvent
from kitchen_commons.models.WaitressServiceModel import Menu
from kitchen_commons.shared.Settings import settings
from kitchen_commons.shared.Logging import logger

class RedisService:

    MENU_CACHE_KEY              = "menu_items"
    
    DEFAULT_TTL_SECONDS         = 3600  # 1 hour
    
    WAITRESS_ORDER_EVENTS       = "waitress_order_events"
    KITCHEN_ORDER_EVENTS        = "kitchen_order_events"
    DEAD_EVENT_QUEUE            = "dead_event_queue"

    KITCHEN_LAST_MESSAGE_ID_KEY   = "kitchen_last_message_id"
    WAITRESS_LAST_MESSAGE_ID_KEY  = "waitress_last_message_id"

    def __init__(self):
        self.client = redis.Redis(host=settings.redis_host, port=settings.redis_port, db=settings.redis_db, decode_responses=True)

    async def generate_new_id(self, counter_key: str) -> int: 
        return await self.client.incr(counter_key) # type: ignore

    async def publish_waitress_order_event(self, base_event: BaseEvent):
        await self._publish_event(self.WAITRESS_ORDER_EVENTS, base_event)

    async def consume_waitress_order_event(self, last_id: str = '0-0'):
        return await self._consume_event(self.WAITRESS_ORDER_EVENTS, last_id)

    async def publish_kitchen_order_event(self, base_event: BaseEvent):
        await self._publish_event(self.KITCHEN_ORDER_EVENTS, base_event)

    async def publish_error_event(self, base_event: BaseEvent):
        await self._publish_event(self.DEAD_EVENT_QUEUE, base_event)

    async def consume_kitchen_order_event(self, last_id: str = '0-0'):
        return await self._consume_event(self.KITCHEN_ORDER_EVENTS, last_id)

    async def _publish_event(self, stream: str, base_event):
        event_data = base_event.to_redis()
        await self.client.xadd(stream, event_data) # type: ignore
        logger.info("Event added to Redis stream", stream=stream, event_data=event_data)

    async def _consume_event(self, stream: str, last_id: str):
        messages = await self.client.xread({stream: last_id}, count=1, block=1000)
        if messages:
            stream, messages_list = messages[0] # type: ignore
            for message_id, message_data in messages_list:
                return message_id, message_data
        else:
            logger.info("No new messages in Redis stream", stream=stream)

    async def set_menu_cache(self, menu: Menu) -> None:
        await self.client.set(self.MENU_CACHE_KEY, menu.model_dump_json(), ex=self.DEFAULT_TTL_SECONDS)
        logger.info("Menu items cached", key=self.MENU_CACHE_KEY)

    async def get_menu_cache(self) -> Optional[Menu]:
        cached_menu = await self.client.get(self.MENU_CACHE_KEY)

        if not cached_menu :
            return None

        logger.info("Menu items fetched from cache under key", key=self.MENU_CACHE_KEY, menu_items=cached_menu)

        try:
            return Menu.model_validate_json(cached_menu) # type: ignore
        except Exception as e:
            logger.error("Error validating cached menu data", error=str(e))
            return None

    async def get_last_kitchen_message_id(self,) -> str:
        last_id = await self.client.get(self.KITCHEN_LAST_MESSAGE_ID_KEY)
        logger.info("Retrieved last kitchen message ID", last_id=last_id)
        return last_id if last_id else "0-0" # type: ignore

    async def set_last_kitchen_message_id(self, last_id: str):
        await self.client.set(self.KITCHEN_LAST_MESSAGE_ID_KEY, last_id)
        logger.info("Saved last kitchen message ID", last_id=last_id)

    async def get_last_waitress_message_id(self,) -> str:
        last_id = await self.client.get(self.WAITRESS_LAST_MESSAGE_ID_KEY)
        logger.info("Retrieved last waitress message ID", last_id=last_id)
        return last_id if last_id else "0-0" # type: ignore

    async def set_last_waitress_message_id(self, last_id: str):
        await self.client.set(self.WAITRESS_LAST_MESSAGE_ID_KEY, last_id)
        logger.info("Saved last waitress message ID", last_id=last_id)

redis_service = RedisService()