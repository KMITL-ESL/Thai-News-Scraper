import asyncio
from asyncio.windows_events import NULL
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


class BangkokbiznewsAgency(Agency):
    def __init__(self, config):
        self.config = config

    def parse_date(self, date_text) -> datetime:
        _, thai_month, thai_year = date_text.split(' ')
        date_text = date_text.replace(
            thai_month, constants.TH_FULL_MONTHS_MAPPER[thai_month])
        date_text = date_text.replace(thai_year, str(int(thai_year) - 543))
        date = datetime.strptime(date_text, r'%d %B %Y')
        return date

    async def call(self, url) -> RawNewsEntity:
        soup = await self.scrap_html(url)

        if soup is None:
            logging.error(f'failed to obtain {url}')
            return

        logging.info(f'scrap {url}')
        soup2 = soup.find('div', attrs={'class': 'col-lg-8 col-md-8 col-sm-12'})

        title = soup.find('h1', attrs={'class': 'section_title section_title_medium_var2'}).text.strip()
        logging.info(title)
        date_text = soup2.find('div', attrs={'class': 'event_date'}).text.strip()
        date = self.parse_date(date_text)
        logging.info(date)
        content = ' '.join(' '.join(list(map(lambda text: text.get_text(), soup2.find_all('p')))).split())
        #tags = None
        #category = tags[-1].text.strip()
        return RawNewsEntity(id=str(uuid.uuid4()),
                             publish_date=date,
                             title=title,
                             content=content,
                             created_at=datetime.now(),
                             source='BANGKOKBIZNEWS',
                             link=url, 
                             )

    async def scrap_links(self, index_url, from_date, to_date, max_news):
        page_number = 1
        all_links = set()
        while len(all_links) < max_news:

            soup = await self.scrap_html(index_url + str(page_number))
            logging.info(f'page {page_number}')
            if soup is None:
                logging.error(f'failed to obtain {index_url + str(page_number)}')
                return

            links = soup.find('div', attrs={'class':'read_post_list'})
            date_texts = soup.find_all('div', attrs={'class': 'event_date'})
            date_texts = list(map(lambda date_text: date_text.text, date_texts))
            links = soup.find_all('h3', attrs={'class':'post_title'})
            links = list(map(lambda link: link.find('a',  href=True), links))

            links = list(map(lambda link: f'{link["href"]}', links))

            dates = list(
                map(lambda date_text: self.parse_date(date_text), date_texts))

            min_date = min(dates)
            max_date = max(dates)

            for date, link in zip(dates, links):
                all_links.add(link)
                logging.info(link)
            if min_date < from_date:
                break

            page_number += 1
        return all_links
    
    async def scrap(self) -> List[RawNewsEntity]:
        index_urls = self.config['indexes']
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

