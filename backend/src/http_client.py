from aiohttp import ClientSession, ClientResponseError
from src.config import settings
import json


class CMCHTTPClient:
    def __init__(self, base_url: str, api_key: str):
        self._session = ClientSession(
            headers={
                settings.API_AUTHORIZATION_HEADER: api_key
            },
            base_url=base_url
        )

    async def get_listings(self) -> list[dict]:
        """ Get list of cryptocurrencies from CoinMarketCap API

        Returns:
            list[dict]: List of cryptocurrencies(dict)
        
        Raises:
            Exception: If any error occurred
        """
        try:
            async with self._session.get('/v1/cryptocurrency/listings/latest') as response:
                result = await response.json()
                timestamp = result['status']['timestamp']
                data = [{**row, 'timestamp': timestamp} for row in result['data']]
                return data
        except (ClientResponseError, json.JSONDecodeError) as e:
            raise Exception(f"Error occurred: {e}")


cmc_client = CMCHTTPClient(
    base_url= settings.BASE_API_URL,
    api_key=settings.CMC_API_KEY
)