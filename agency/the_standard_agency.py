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


class TheStandardAgency(Agency):
    def __init__(self, config):
        self.config = config

    def parse_date_index(self, date_text) -> datetime:

        date_text = ' '.join(date_text.strip().split(' '))
        date_text = date_text.replace('\n', '')
        _, thai_month, thai_year, *_ = date_text.split(' ')
        date_text = date_text.replace(
            thai_month, constants.TH_FULL_MONTHS_MAPPER[thai_month])
        date = datetime.strptime(date_text, r'%d %B %Y')
        return date

    def parse_date(self, date_text) -> datetime:

        date_text = date_text.replace('.', ' ')
        date = datetime.strptime(date_text, r'%d %m %Y')
        return date

    async def scrap_links(self, index_url, from_date, to_date, max_news):

        all_links = set()
        for page_number in range(1, (max_news//constants.NEWS_MAX_NUM_PER_PAGE)+1):
            soup = await self.scrap_html(index_url+'page/'+str(page_number))
            if soup is None:
                logging.error(
                    f'failed to obtain {index_url} with page {page_number}')
                continue
            try:
                logging.info(f'page {page_number}') 
                articles = soup.find('div', attrs={'class': 'newsbox-archive'})
                date_texts = soup.find_all('div', attrs={'class': 'date'})
                date_texts = list(map(lambda date_text: date_text.text, date_texts))
                articles = articles.find_all('div', attrs={'class':'news-item'})
                articles = list(map(lambda article: article.find('h3', attrs={'class':'news-title'}), articles))
                articles = list(map(lambda link: link.find('a',  href=True), articles))
                dates = list(map(lambda date_text: self.parse_date_index(date_text), date_texts))
                min_date = min(dates)
                max_date = max(dates)
                links = list(map(lambda link: f'{link["href"]}', articles))
            except:
                continue

            for date, link in zip(dates, links):
                soup = await self.scrap_html(link) 
                try:
                    category_dl = soup.find('span', attrs={'class': 'category'}).text.strip()
                except:
                    logging.info(f'Error : {link}')
                    continue
                category_dl = category_dl.split('/')[0].lower().strip().replace(' ', '').replace('&','-')
                if  soup.find('div', attrs={'class':'meta-date'}) is not None and soup.find('h1', 
                attrs={'class': 'title'}).text.strip().find('ชมคลิป:') == -1 and category_dl not in constants.CATEGORY_DELETE_THESTANDARD:
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
        tags = soup.find('meta', attrs={'name': 'Keywords'})
        tags = f'{tags["content"]}'.replace(' ', '').split(',')[:-1]
        tags = ','.join(tags)
        try:
            category = soup.find('span', attrs={'class': 'category'}).text.strip()
            category = category.split('/')[0].lower().strip().replace(' ', '').replace('&','-')
        except:
            logging.info(f'Something went wrong')
        finally:
            logging.info(f'{category}')
            logging.info(f'{tags}')
        title = soup.find('h1', attrs={'class': 'title'}).text.strip()
        date_text = soup.find('div', attrs={'class': 'meta-date'}).text.strip()
        date = self.parse_date(date_text)
        content = soup.find('div', attrs={'class': 'col-sm-9 fix-sticky'
                  }).find('div', attrs={'class': 'entry-content'}).text.strip()

        return RawNewsEntity(publish_date=date,
                             title=title,
                             content=content,
                             created_at=datetime.now(),
                             source='THE STANDARD',
                             link=url,
                             category=category,
                             tags=tags
                             )

    async def scrap(self) -> List[RawNewsEntity]:
        index_urls = self.config['indexes_the_standard']
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
