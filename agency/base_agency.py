import asyncio

import aiohttp
from bs4 import BeautifulSoup


class Agency:
    async def scrap_html(self, url, params=None) -> BeautifulSoup:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as res:
                return BeautifulSoup(await res.text(), features="html.parser")
    async def call(self, url):
        pass
    async def scrap_links(self):
        pass