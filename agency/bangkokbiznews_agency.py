import asyncio
import logging
from os import replace
import uuid
from datetime import datetime, timedelta
from typing import List
from urllib.parse import urlparse
import attr

import requests
from bs4 import BeautifulSoup
from config import config
from model import RawNewsEntity
from util import constants

from agency import Agency


class BkkbiznewsAgency(Agency):
    def __init__(self, config):
        self.config = config

    def parse_date(self, date_text) -> datetime:
        
        date_text = (date_text.split(' '))[0:3]
        date_text = ' '.join(date_text)
        date_text = date_text.replace('\n', '')
        date_text = date_text.replace('|', '')
        _, thai_month, thai_year, *_ = date_text.split(' ')
        date_text = date_text.replace(
            thai_month, constants.TH_FULL_MONTHS_MAPPER[thai_month])
        date_text = date_text.replace(thai_year, str(int(thai_year) - 543))
        date = datetime.strptime(date_text, r'%d %B %Y')
        return date

    async def scrap_links(self, index_url, from_date, to_date, max_news):

        all_links = set()
        for page_number in range(1, (max_news//constants.NEWS_MAX_NUM_PER_PAGE)+1):

            soup = await self.scrap_html(index_url+str(page_number) , params={'page': page_number})
            if soup is None:
                logging.error(
                    f'failed to obtain {index_url} with page {page_number}')
                continue
            logging.info(f'page {page_number}')
            articles = soup.find('div', attrs={'class':'read_post_list'})
            date_texts = soup.find_all('div', attrs={'class': 'event_date'})
            date_texts = list(map(lambda date_text: date_text.text, date_texts))
            articles = soup.find_all('h3', attrs={'class':'post_title'})
            articles = list(map(lambda link: link.find('a',  href=True), articles))
            dates = list(
                map(lambda date_text: self.parse_date(date_text), date_texts))
            
            min_date = min(dates)
            max_date = max(dates)

            links = list(
                map(lambda link: f'{link["href"]}', articles))

            for date, link in zip(dates, links):
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

        soup_news = soup.find('div', attrs={'class': 'col-lg-8 col-md-8 col-sm-12'})
        title = soup.find('h1', attrs={'class': 'section_title section_title_medium_var2'}).text.strip()
        date_text = soup_news.find('div', attrs={'class': 'event_date'}).text.strip()
        date = self.parse_date(date_text)
        content = ' '.join(' '.join(list(map(lambda text: text.get_text(), soup_news.find_all('p')))).split())
        
        return RawNewsEntity(publish_date=date,
                             title=title,
                             content=content,
                             created_at=datetime.now(),
                             source='BKKBIZNEWS',
                             link=url
                             )

    async def scrap(self) -> List[RawNewsEntity]:
        index_urls = self.config['indexes_bkkbiznews']
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
