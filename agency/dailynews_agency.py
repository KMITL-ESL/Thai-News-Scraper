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


class DailynewsAgency(Agency):
    def __init__(self, config):
        self.config = config

    def parse_date(self, date_text) -> datetime:

        date_text = ' '.join(date_text.strip().split(' ')[:-1])
        date_text = date_text.replace('น.', '')
        date_text = date_text.replace(':', '.')
        date_text = date_text.replace('\n', '')
        date_text = date_text.replace('\t', '')
        _, thai_month, thai_year, *_ = date_text.split(' ')
        date_text = date_text.replace(
            thai_month, constants.TH_FULL_MONTHS_MAPPER[thai_month])
        date_text = date_text.replace(thai_year, str(int(thai_year) - 543))
        date = datetime.strptime(date_text, r'%d %B %Y %H.%M')
        return date

    async def scrap_links(self, index_url, from_date, to_date, max_news):

        all_links = set()
        for page_number in range(1, (max_news//constants.NEWS_MAX_NUM_PER_PAGE)+1):

            soup = await self.scrap_html(index_url+'page/'+str(page_number), params={'page': page_number})
            if soup is None:
                logging.error(
                    f'failed to obtain {index_url} with page {page_number}')
                continue
            
            logging.info(f'page {page_number}')
            
            articles = soup.find_all('a', attrs={'class': 'elementor-post__thumbnail__link'}, href=True)
            date_texts = soup.find_all('div', attrs={'class': 'elementor-post__meta-data'})
            date_texts = list(map(lambda date_text: date_text.find(
                'span', attrs={'class': 'elementor-post-date'}).text+' '+
                date_text.find('span', attrs={'class': 'elementor-post-time'}).text, date_texts))
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

        title = soup.find('h1', attrs={'class': 'elementor-heading-title elementor-size-default'}).text.strip()
        date_text = soup.find('span', 
                    attrs={'class': 'elementor-icon-list-text elementor-post-info__item elementor-post-info__item--type-date'}).text.strip()+' '+soup.find('span', 
                    attrs={'class': 'elementor-icon-list-text elementor-post-info__item elementor-post-info__item--type-time'}).text.strip()
        date = self.parse_date(date_text)
        content = soup.find('div', attrs={'class': 'elementor-element elementor-element-31c4a6f post-content elementor-widget elementor-widget-theme-post-content'
                  }).find('div', attrs={'class': 'elementor-widget-container'}).text.strip()
        category = url.split("/")[3]

        return RawNewsEntity(publish_date=date,
                             title=title,
                             content=content,
                             created_at=datetime.now(),
                             source='DAILYNEWS',
                             link=url,
                             category=category
                             )

    async def scrap(self) -> List[RawNewsEntity]:
        index_urls = self.config['indexes_dailynews']
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
