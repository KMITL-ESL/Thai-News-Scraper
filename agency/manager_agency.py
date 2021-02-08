import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import List
from urllib.parse import urlparse
import numpy as np
from bs4 import BeautifulSoup
from config import config
from model import RawNewsEntity
from util import constants

from agency import Agency


class ManagerAgency(Agency):

    async def __scrap_sub_index_links(self, sub_index_url) -> List[str]:
        soup = await self.scrap_html(sub_index_url)
        if soup is None:
            logging.error(
                f'failed to obtain {sub_index_url} ')
            return []

        news_link_elements = soup.find(
            'div', attrs={'class': 'search-display-result'}).find_all('a')
        news_links = list(
            map(lambda ele: ele['href'], news_link_elements))
        return news_links

    async def scrap_links(self, index_url) -> List[str]:
        index_soup = await self.scrap_html(index_url)
        if index_soup is None:
            logging.error(
                f'failed to obtain {index_url}')
            return []
        header_elements = index_soup.find_all(
            'header', attrs={'class': 'category-topic'})
        sub_index_urls = list(
            map(lambda ele: ele.find('a')['href'], header_elements))

        # remove query param
        sub_index_urls = list(
            map(lambda url: url[: url.find('/start=')], sub_index_urls))

        links = []

        sub_index_page_urls = []
        for sub_index_url in sub_index_urls:
            for start in np.arange(0, 200, 10):
                url = f'{sub_index_url}/start={str(start)}'
                sub_index_page_urls.append(url)

        sub_urls = await asyncio.gather(
            *[self.__scrap_sub_index_links(url) for url in sub_index_page_urls])
        
        return sum(sub_urls, [])

    async def call(self, url) -> RawNewsEntity:
        soup = await self.scrap_html(url)
        if soup is None:
            logging.error(f'failed to obtain {url}')
            return

        title = soup.find('h1').text.strip()

        date_text = soup.find(
            'header', attrs={'class': 'header-article'}).find('time').text.strip()
        _, thai_symbol_month, thai_year, *_ = date_text.split(' ')
        date_text = date_text.replace(
            thai_symbol_month, constants.TH_SYMBOL_MONTHS_MAPPER[thai_symbol_month])
        date_text = date_text.replace(thai_year, str(int(thai_year) - 543))
        date = datetime.strptime(date_text, r'%d %B %Y %H:%M')

        content = ''
        content_element = soup.find('div', attrs={'class': 'detail'})
        for ele in content_element.find_all('strong'):
            for child in ele.find_all():
                child.extract()
            content += ele.text

        return RawNewsEntity(publish_date=date,
                             title=title,
                             content=content,
                             created_at=datetime.now(),
                             source='MANAGERONLINE',
                             link=url)

    async def scrap(self) -> List[RawNewsEntity]:
        links = set()
        for index_url in self.config['indexes']:
            _links = await self.scrap_links(index_url)
            links.update(_links)

        logging.info(f'number of link = {len(links)}')
        return asyncio.gather(*[self.call(link) for link in links])
