from aiohttp import ClientSession


class CMCHTTPClient:
    def __init__(self, base_url: str, api_key: str):
        self._session = ClientSession(
            headers={
                'X-CMC_PRO_API_KEY': api_key
            },
            base_url=base_url
        )  
    
    async def get_listings(self):
        async with self._session.get('/v1/cryptocurrency/listings/latest') as response:
            result =  await response.json()
            return result['data']
    
    async def get_currency(self, currency_id: int):
        async with self._session.get(
            '/v2/cryptocurrency/quotes/latest',
            params = {'id': currency_id}
        ) as response:
            result = await response.json()
            return result['data'][str(currency_id)]

    