import aiohttp

HOROSCOPE_API_URL = "https://freehoroscopeapi.com/api/v1/get-horoscope/daily"

async def get_daily_horoscope(sign):
    async with aiohttp.ClientSession() as session:
        async with session.get(HOROSCOPE_API_URL, params={"sign": sign}) as resp:
            result = await resp.json()
            return result["data"]["horoscope"]
