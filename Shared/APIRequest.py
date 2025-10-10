import asyncio
from enum import Enum
from typing import Any
from .Logging import logger
import httpx

class APIRequest:

    class Method(Enum):
        POST = "POST"
        GET = "GET"
        PUT = "PUT"
        DELETE = "DELETE"

    MAX_RETRY_COUNT = 5
    RETRY_DELAY_SECONDS = 2 # Delay between retries

    def __init__(self, method: Method, url: str, payload: Any | None = None):
        self.method = method
        self.url = url
        self.payload = payload

    async def sendRequest(self):

        logger.info("Sending API request", method=self.method, url=self.url, payload=self.payload)

        for attempt in range(self.MAX_RETRY_COUNT):
            try:
                async with httpx.AsyncClient() as client:
                    if self.method == self.Method.GET:
                        response = await client.get(self.url)
                    elif self.method == self.Method.POST:
                        response = await client.post(self.url, json=self.payload)
                    elif self.method == self.Method.PUT:
                        response = await client.put(self.url, json=self.payload)
                    elif self.method == self.Method.DELETE:
                        response = await client.delete(self.url)
                    else:
                        logger.error("Unsupported HTTP method", method=self.method)
                        raise ValueError(f"Unsupported HTTP method: {self.method}")

                    response.raise_for_status()  # Raise an error for bad responses

                logger.info("API request successful", status_code=response.status_code, response=response.json())
                return response

            except httpx.RequestError as e:
                logger.error("Request error occurred", error=str(e))
            except httpx.HTTPStatusError as e:
                logger.error("HTTP status error occurred", status_code=e.response.status_code, error=str(e))

            logger.info("Retrying in %d seconds... (Attempt %d/%d)", self.RETRY_DELAY_SECONDS, attempt + 1, self.MAX_RETRY_COUNT)
            await asyncio.sleep(self.RETRY_DELAY_SECONDS)