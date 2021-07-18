import asyncio
from typing import List
from datetime import datetime

import aiohttp
from bs4 import BeautifulSoup
from model import RawNewsEntity


class Agency:
    async def scrap_html(self, url: str, params=None) -> BeautifulSoup:
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(url, params=params) as res:
                    return BeautifulSoup(await res.text(), features="html.parser")
            except:
                return

    async def scrap_links(self) -> List[str]:
        pass

    async def call(self, url: str) -> RawNewsEntity:
        pass

    async def scrap(self, from_date: datetime, to_date: datetime) -> List[RawNewsEntity]:
        pass
