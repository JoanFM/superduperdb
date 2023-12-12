import requests
import aiohttp
from aiohttp import ClientResponseError, ClientConnectionError

from typing import Optional, List
from superduperdb.misc.retry import Retry
from superduperdb.ext.utils import get_key
from requests.exceptions import HTTPError


JINA_API_URL: str = "https://api.jina.ai/v1/embeddings"
KEY_NAME = 'JINA_API_KEY'

retry = Retry(exception_types=(ClientResponseError, ClientConnectionError, HTTPError))


class JinaAPIClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = 'jina-embeddings-v2-base-en',
    ):
        """
        Create a JinaAPIClient to provide an interface to encode using Jina Embedding platform sync and async.

        :param api_key: The Jina API key. It can be explicitly provided or automatically read from the
            environment variable JINA_API_KEY (recommended).
        :param model_name: The name of the Jina model to use. Check the list of available models on `https://jina.ai/embeddings/`
        # if the user does not provide the API key, check if it is set in the module client
        """
        if api_key is None:
            api_key = get_key(KEY_NAME)

        self.model_name = model_name
        self._session = requests.Session()
        self._headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept-Encoding": "identity",
            "Content-type": "application/json",
        }
        self._session.headers.update(self._headers)

    @retry
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        response = self._session.post(
            JINA_API_URL, json={"input": texts, "model": self.model_name}
        ).json()
        if "data" not in response:
            raise RuntimeError(response["detail"])

        # Sort resulting embeddings by index
        sorted_embeddings = sorted(response["data"], key=lambda e: e["index"])
        embeddings = [result["embedding"] for result in sorted_embeddings]
        return embeddings

    @retry
    async def aencode_batch(self, texts: List[str]) -> List[List[float]]:
        async with aiohttp.ClientSession() as session:
            payload = {
                'model': self.model_name,
                'input': texts,
            }

            async with session.post(
                JINA_API_URL,
                headers=self._headers,
                json=payload,
            ) as response:
                response.raise_for_status()
                response_json = await response.json()
                if "data" not in response_json:
                    raise RuntimeError(response_json["detail"])

                # Sort resulting embeddings by index
                sorted_embeddings = sorted(
                    response_json["data"], key=lambda e: e["index"]
                )
                embeddings = [result["embedding"] for result in sorted_embeddings]
                return embeddings
