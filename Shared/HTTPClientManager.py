from typing import Optional
import httpx

class HTTPClientManager:

    def __init__(self):
        self._client: Optional[httpx.AsyncClient] = None

    async def start(self):
        self._client = httpx.AsyncClient(
            timeout=30.0
        )

    async def stop(self):
        self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None:
            raise RuntimeError("HTTPx client is not started!")
        return self._client
    
http_client_manager = HTTPClientManager()