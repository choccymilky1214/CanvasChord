import aiohttp
import asyncio

async def test_https():
    async with aiohttp.ClientSession() as session:
        async with session.get('https://www.google.com') as response:
            print(await response.text())

if __name__ == "__main__":
    asyncio.run(test_https())
