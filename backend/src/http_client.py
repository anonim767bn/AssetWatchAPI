"""This module contains the CMCHTTPClient class which is used to interact with the CoinMarketCap API."""

import json

from aiohttp import ClientResponseError, ClientSession

from src.config import settings


class CMCHTTPClient:
    """
    HTTP client for CoinMarketCap API.

    Attributes:
        _session (ClientSession): aiohttp client session.
    """

    def __init__(self, base_url: str, api_key: str):
        """
        Initialize the CMCHTTPClient.

        Args:
            base_url (str): The base URL for the API.
            api_key (str): The API key for authentication.
        """
        self._session = None
        self._base_url = base_url
        self._api_key = api_key

    async def start(self) -> None:
        self._session = ClientSession(
            headers={
                settings.API_AUTHORIZATION_HEADER: self._api_key
            },
            base_url=self._base_url
        )

    async def stop(self) -> None:
        if self._session:
            await self._session.close()

    async def get_listings(self) -> list[dict]:
        """
        Get list of cryptocurrencies from CoinMarketCap API.

        Returns:
            list[dict]: List of cryptocurrencies(dict).

        Raises:
            Exception: If any error occurred.
        """
        await self.start()
        try:
            async with self._session.get('/v1/cryptocurrency/listings/latest') as response:
                response_json = await response.json()
                timestamp = response_json['status']['timestamp']
                return [{**row, 'timestamp': timestamp} for row in response_json['data']]
        except (ClientResponseError, json.JSONDecodeError) as error:
            raise Exception(f'Error occurred: {error}')
        finally:
            await self.stop()


# Initialize the CoinMarketCap HTTP client
cmc_client = CMCHTTPClient(
    base_url=settings.BASE_API_URL,
    api_key=settings.CMC_API_KEY,
)
