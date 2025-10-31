import asyncio
from enum import Enum
from typing import Any
from shared.Logging import logger
from shared.HTTPClientManager import http_client_manager
import httpx
import logging
from tenacity import (
    retry, 
    stop_after_attempt, 
    wait_exponential,
    retry_if_exception,
    before_sleep_log,
    after_log
)

class APIRequest:

    class Method(Enum):
        POST = "POST"
        GET = "GET"
        PUT = "PUT"
        DELETE = "DELETE"

    def __init__(self, method: Method, url: str, payload: Any | None = None):
        self.method = method
        self.url = url
        self.payload = payload

    @retry(
        stop=stop_after_attempt(5), 
        wait=wait_exponential(multiplier=2, min=1, max=10),
        reraise=True,
        before_sleep=before_sleep_log(logger, logging.WARNING),
        after=after_log(logger, logging.INFO)
    )
    async def sendRequest(self) -> httpx.Response:

        logger.info("Sending API request", method=self.method, url=self.url, payload=self.payload)

        client = http_client_manager.client
    
        if self.method == self.Method.GET:
            response = await client.get(self.url)
        elif self.method == self.Method.POST:
            response = await client.post(self.url, json=self.payload)
        else:
            logger.error("Unsupported HTTP method", method=self.method)
            raise ValueError(f"Unsupported HTTP method: {self.method}")

        response.raise_for_status()  # Raise an error for bad responses

        logger.info("API request successful", status_code=response.status_code, response=response.json())
        return response
