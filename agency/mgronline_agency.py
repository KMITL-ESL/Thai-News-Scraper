import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import List
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from config import config
from model import RawNewsEntity
from util import constants

from agency import Agency


class MgronlineAgency(Agency):
    def __init__(self, config):
        self.config = config

    def parse_date(self, date_text) -> datetime:
        date_text = ' '.join(date_text.strip().split(' '))
        date_text = date_text.replace('/', ' ')
        date_text = date_text.replace(':', '.')
        date_text = date_text.replace('\t', '')
        _, thai_month, thai_year, *_ = date_text.split(' ')
        date_text = date_text.replace(
            thai_month, constants.TH_FULL_MONTHS_MAPPER_MGR[thai_month])
        date_text = date_text.replace(thai_year, str(int(thai_year) - 543))
        date = datetime.strptime(date_text, r'%d %B %Y %H.%M')
        return date

    def parse_date_index(self, date_text) -> datetime:

        date_text = ' '.join(date_text.strip().split(' '))
        date_text = date_text.replace('/', ' ')
        date_text = date_text.replace(':', '.')
        date = datetime.strptime(date_text, r'%Y %m %d %H.%M.%S')
        return date
        
    async def scrap_links(self, index_url, from_date, to_date, max_news):

        all_links = set()
        for page_number in range(0, (max_news//constants.NEWS_MAX_NUM_PER_PAGE)):
        #for page_number in range(0, 39):
            soup = await self.scrap_html(index_url+'start='+str(page_number*10), params={'page': page_number})
            if soup is None:
                logging.error(
                    f'failed to obtain {index_url} with page {page_number}')
                continue

            logging.info(f'page {page_number}')
            articles = soup.find_all('a',attrs={'class':'link'}, href=True)
            date_texts = soup.find_all('time', attrs={'class':'p-date-time-item'})
            date_texts = list(map(lambda date_text: date_text['data-pdatatimedata'], date_texts))
            dates = list(
                map(lambda date_text: self.parse_date_index(date_text), date_texts))
            min_date = min(dates)
            max_date = max(dates)
            links = list(
                map(lambda link: f'{link["href"]}', articles))
            for date, link in zip(dates, links):
                if soup.find_all('time', attrs={'class':'p-date-time-item'}) is not None:
                    all_links.add(link)
                    logging.info(link)
            if min_date < from_date:
                break
        return all_links

    async def call(self, url) -> RawNewsEntity:
        soup = await self.scrap_html(url)
        if soup is None:
            logging.error(f'failed to obtain {url}')
            return

        logging.info(f'scrap {url}')

        title = soup.find('header', attrs={'class': 'header-article'})
        title = soup.find('h1').text.strip()
        date_text = soup.find('time').text.strip()
        date = self.parse_date(date_text)
        logging.info(date)
        content = soup.find('div', attrs={'class': 'article-content'}).text.strip()
        return RawNewsEntity(publish_date=date,
                             title=title,
                             content=content,
                             created_at=datetime.now(),
                             source='MANAGERONLINE',
                             link=url
                             )

    async def scrap(self) -> List[RawNewsEntity]:
        index_urls = self.config['indexes_mgronline']
        links = set()
        for index_url in index_urls:
            _links = await self.scrap_links(index_url,
                                            from_date=datetime.now() -
                                            timedelta(
                                                days=self.config['since_datedelta']),
                                            to_date=datetime.now(),
                                            max_news=self.config['max_news_per_batch'])
            links.update(_links)

        logging.info(f'number of link = {len(links)}')
        entities = await asyncio.gather(*[self.call(link) for link in links])
        return list(filter(lambda entity: entity is not None, entities))
