import asyncio
import logging
from datetime import datetime
from typing import List

import aiohttp
from bs4 import BeautifulSoup
from model import RawNewsEntity


class Agency:
    def __init__(self, config):
        self.config = config
        self._max_concurrent = self.config.get('max_concurrent', 100)
        print(self.__class__, self._max_concurrent)
        self._tcp_connector = aiohttp.TCPConnector(limit_per_host=self._max_concurrent)

        # self._session = aiohttp.ClientSession(connector=self._tcp_connector)

    async def scrap_html(self, url: str, params=None) -> BeautifulSoup:

        
        async with aiohttp.ClientSession(connector=self._tcp_connector) as session:
            async with session.get(url, params=params) as res:
                logging.info(f'scrap {url}')
                return BeautifulSoup(await res.text(), features="html.parser")

        # async with self._session.get(url, params=params) as res:
        #     return BeautifulSoup(await res.text(), features="html.parser")


    async def scrap_links(self) -> List[str]:
        pass

    async def call(self, url: str) -> RawNewsEntity:
        pass

    async def scrap(self,) -> List[RawNewsEntity]:
        pass
