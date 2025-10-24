from .RedisService import redis_service
from .HTTPClientManager import http_client_manager
from .Logging import logger

async def startup_http_client():
    logger.info("Starting http client manager...")
    await http_client_manager.start()
    logger.info("Http client manager has been started")

async def shutdown_http_client():
    logger.info("Shutting down http client manager...")
    await http_client_manager.stop()
    logger.info("http client manager is shut down...")

async def startup_redis():
    logger.info("Starting Redis...")
    await redis_service.client.ping()
    logger.info("Reddis connected...")

async def shutdown_redis():
    logger.info("Closing Redis connection...")
    await redis_service.client.close()
    logger.info("Redis connection closed...")