import asyncio

import aiohttp
from bs4 import BeautifulSoup
from model import RawNewsEntity


class Agency:
    async def scrap_html(self, url, params=None) -> BeautifulSoup:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, params=params) as res:
                return BeautifulSoup(await res.text(), features="html.parser")
    async def call(self, url)-> RawNewsEntity:
        pass
    async def scrap_links(self):
        pass
