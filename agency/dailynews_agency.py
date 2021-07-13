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


class DailynewsAgency(Agency):
    def __init__(self, config):
        self.config = config

    def parse_date(self, date_text) -> datetime:

        # Trim date name and น.
        #date_text = ' '.join(date_text.strip().split(' ')[1:-1])
        #date_text = date_text.replace('เวลา', '')  # remove เวลา
        #date_text = date_text.replace('  ', ' ')
        _, thai_month, thai_year, *_ = date_text.split(' ')
        date_text = date_text.replace(
            thai_month, constants.TH_FULL_MONTHS_MAPPER[thai_month])
        date_text = date_text.replace(thai_year, str(int(thai_year) - 543))
        date = datetime.strptime(date_text, r'%d %B %Y %H.%M')
        return date

    async def call(self, url) -> RawNewsEntity:
        soup = await self.scrap_html(url)

        if soup is None:
            logging.error(f'failed to obtain {url}')
            return

        logging.info(f'scrap {url}')

        title = soup.find('h1', attrs={'class': 'elementor-heading-title elementor-size-default'}).text.strip()
        date_text = (soup.find('span', attrs={'class': 'elementor-icon-list-text elementor-post-info__item elementor-post-info__item--type-date'}).text.strip() + ' ' + soup.find('span', attrs={'class': 'elementor-icon-list-text elementor-post-info__item elementor-post-info__item--type-time'}).text.strip()).replace(' น.', '').replace(':', '.')
        date = self.parse_date(date_text)
        logging.info(date)
        content = soup.find('div', attrs={'class': 'elementor-element elementor-element-31c4a6f post-content elementor-widget elementor-widget-theme-post-content'}).text.strip().replace('\n', '')
        tags = soup.find('span', attrs={'class': 'elementor-icon-list-text elementor-post-info__item elementor-post-info__item--type-terms'}).text.strip()
        category = tags[-1].text.strip()
        return RawNewsEntity(id=str(uuid.uuid4()),
                             publish_date=date,
                             title=title,
                             content=content,
                             created_at=datetime.now(),
                             source='DAILYNEWS',
                             link=url, 
                             )

    async def scrap_links(self, index_url, from_date, to_date, max_news):
        root_url = urlparse(index_url).hostname
        topic = index_url.split('/')[-1]

        page = 'page/'
        page_number = 1
        all_links = set()
        while len(all_links) < max_news:

            soup = await self.scrap_html(index_url + page + str(page_number))
            logging.info(f'page {page_number}')
            if soup is None:
                logging.error(f'failed to obtain {index_url + page + str(page_number)}')
                return
            div = soup.find('div', attrs={'class': 'elementor-element elementor-element-3c67710c elementor-grid-1 elementor-posts--thumbnail-left elementor-grid-tablet-1 archive-more-post elementor-grid-mobile-1 elementor-widget elementor-widget-posts'})
            
            articles = div.find_all('a', attrs={'class': 'elementor-post__thumbnail__link'}, href=True)
            links = list(map(lambda link: f'{link["href"]}', articles))

            date_texts = div.find_all('div', attrs={'class': 'elementor-post__meta-data'})
            date_texts = list(map(lambda date_text: date_text.find(
                'span', attrs={'class': 'elementor-post-date'}).text + ' ' +
                date_text.find(
                'span', attrs={'class': 'elementor-post-time'}).text, date_texts))
            date_texts = list(map(lambda date_text: date_text.replace('\n', '').replace('\t', ''), date_texts))
            date_texts = list(map(lambda date_text: date_text.replace(' น.', '').replace(':', '.'), date_texts))

            dates = list(
                map(lambda date_text: self.parse_date(date_text), date_texts))

            min_date = min(dates)
            max_date = max(dates)

            logging.info(from_date)

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

