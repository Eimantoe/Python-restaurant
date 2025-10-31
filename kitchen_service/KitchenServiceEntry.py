import asyncio
import os
import sys

from kitchen_commons.shared.Lifecycle import startup_http_client, startup_redis, shutdown_redis, shutdown_http_client

#sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


from contextlib import asynccontextmanager
from .KitchenServiceLogic import KitchenServiceLogic

from fastapi import FastAPI, status

from kitchen_commons.shared.Logging import logger

@asynccontextmanager
async def lifespan(app: FastAPI):

    logger.info("########################################################################")
    logger.info("##              Kitchen service is starting up...                     ##")
    logger.info("########################################################################")

    await startup_http_client()
    await startup_redis()

    # Use the async factory to create the instance
    kitchen_service_logic = await KitchenServiceLogic.create()  
    # Start the background task to consume waitress order events
    asyncio.create_task(kitchen_service_logic.consume_waitress_order_events())

    yield

    await shutdown_http_client()
    await shutdown_redis()

    logger.info("########################################################################")
    logger.info("##              Kitchen service shutting down...                      ##")
    logger.info("########################################################################")

app = FastAPI(title="Kitchen service", lifespan=lifespan)
