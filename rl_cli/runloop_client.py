import json
import logging
from typing import Any, Dict

from httpx import (
    AsyncClient,
    Response,
)

logger = logging.getLogger(__name__)
_timeout = 30


class RunloopClient:
    def __init__(self, api_key: str, base_url: str):
        self.headers = {"Authorization": f"Bearer {api_key}"}
        self.base_url = base_url

    async def devbox_create_ssh_key(self, id: str) -> Dict[str, Any]:
        async with AsyncClient() as client:
            response = await client.post(
                url=f"{self.base_url}/v1/devboxes/{id}/create_ssh_key",
                headers=self.headers,
                json={},
                timeout=60,
            )
        return self._response_json(response)

    def _response_json(self, response: Response) -> Dict[str, Any]:
        try:
            response_json = response.json()
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing response: {e}")
            logger.error(
                f"Raw response: [status-{response.status_code}] {response.text}"
            )
            raise e
        return response_json
