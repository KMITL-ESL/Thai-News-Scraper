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


class MatichonAgency(Agency):
    def __init__(self, config):
        self.config = config

    def parse_date(self, date_text) -> datetime:

        date_text = ' '.join(date_text.strip().split(' ')[1:-1])
        date_text = date_text.replace('วันที่', '')
        date_text = date_text.replace('น.', '')
        date_text = date_text.replace(':', '.')
        date_text = date_text.replace('-', '')
        date_text = date_text.replace('  ', ' ')
        _, thai_month, thai_year, *_ = date_text.split(' ')
        date_text = date_text.replace(
            thai_month, constants.TH_FULL_MONTHS_MAPPER[thai_month])
        date_text = date_text.replace(thai_year, str(int(thai_year) - 543))
        date = datetime.strptime(date_text, r'%d %B %Y %H.%M')
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
                articles = soup.find('div', attrs={'class', 'td-ss-main-content'})
                date_texts = (articles.find_all('span', attrs={'class': 'td-post-date'}))
                date_texts = list(map(lambda date_text: date_text.find('time',attrs={'class': 
                    'entry-date updated td-module-date'}).text, date_texts))
                articles = soup.find_all('a',attrs={'class':'ud-module-link'}, href=True)
                dates = list(map(lambda date_text: self.parse_date(date_text), date_texts))
                min_date = min(dates)
                max_date = max(dates)
                links = list(map(lambda link: f'{link["href"]}', articles))
            except:
                continue

            for date, link in zip(dates, links):
                soup = await self.scrap_html(link)
                try:
                    category_dl = soup.find('div', attrs={'class': 'entry-crumbs'}).find_all('span', attrs={'class': ''})
                    title_dl = soup.find('h1', attrs={'class': 'entry-title'}).text.strip()
                except:
                    logging.info(f'Error : {link}')
                    continue
                category_dl = category_dl[-1].text
                if category_dl not in constants.CATEGORY_DELETE_MATICHON and title_dl.find('การ์ตูนรุทธ์') == -1:
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

        title = soup.find('h1', attrs={'class': 'entry-title'}).text.strip()
        date_text = soup.find('span', 
                    attrs={'class': 'td-post-date td-post-date-no-dot'}).text.strip()
        date = self.parse_date(date_text)
        content = soup.find('div', attrs={'class': 'td-post-content'}).text.strip()
        category = soup.find('div', attrs={'class': 'entry-crumbs'}).find_all('span', attrs={'class': ''})
        category = category[-1].text
        sub_category = soup.find('div', attrs={'class': 'entry-crumbs'})
        try:
            category = constants.MATICHON_CATEGORY_MAPPER[category]
            content = content.split('\n')
            content = list(map(lambda a: a.strip(), content))
            while '' in content:
                content.remove('')
            content = '\n'.join(content)
            sub_category = sub_category.find_all('span')
            sub_category = list(map(lambda s: s.text.strip(), sub_category))
            sub_category = sub_category[2:-1]
            sub_category = ','.join(sub_category)
            tags = None
        except:
            logging.info(f'Something went wrong')
        finally:
            logging.info(f'{category}')
            if sub_category == '':
                sub_category = None
            logging.info(f'{sub_category}')

        return RawNewsEntity(publish_date=date,
                             title=title,
                             content=content,
                             created_at=datetime.now(),
                             source='MATICHON',
                             link=url,
                             category=category,
                             tags=tags,
                             sub_category=sub_category
                             )

    async def scrap(self) -> List[RawNewsEntity]:
        index_urls = self.config['indexes_matichon']
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
