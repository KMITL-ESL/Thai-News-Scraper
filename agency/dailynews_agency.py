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
        for page_number in range(1, (max_news//constants.DAILYNEWS_MAX_NUM_PER_PAGE)+1):
            soup = await self.scrap_html(index_url+'page/'+str(page_number))
            if soup is None:
                logging.error(
                    f'failed to obtain {index_url} with page {page_number}')
                continue
            try:
                logging.info(f'page {page_number}')
                articles = soup.find_all('a', attrs={'class': 'elementor-post__thumbnail__link'}, href=True)
                date_texts = soup.find_all('div', attrs={'class': 'elementor-post__meta-data'})
                date_texts = list(map(lambda date_text: date_text.find(
                'span', attrs={'class': 'elementor-post-date'}).text+' '+
                date_text.find('span', attrs={'class': 'elementor-post-time'}).text, date_texts))
                dates = list(map(lambda date_text: self.parse_date(date_text), date_texts))
                links = list(map(lambda link: f'{link["href"]}', articles))
                min_date = min(dates)
                max_date = max(dates)
            except:
                continue
            
            for date, link in zip(dates, links):
                soup = await self.scrap_html(link)
                try:
                    title = soup.find('h1',attrs={'class': 'elementor-heading-title elementor-size-default'}).text.strip()
                    category_dl = soup.find('span', attrs={'class': 'elementor-post-info__terms-list'}).find_all('a',attrs={'class':'elementor-post-info__terms-list-item'})
                except:
                    logging.info(f'Error : {link}')
                    continue
                category_dl = category_dl[0].text
                if title.find('รู้หรือไม่') == -1 and title.find('คลิป') == -1 and category_dl is not None and category_dl not in constants.CATEGORY_DELETE_DAILYNEWS:
                    all_links.add(link)
                    logging.info(link)
            # if min_date < from_date:
            #     break

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
        content = soup.find('div', attrs={'data-widget_type': 'theme-post-content.default'
                  }).find('div', attrs={'class': 'elementor-widget-container'}).text.strip()
        category = soup.find('span', attrs={'class': 'elementor-post-info__terms-list'}).find('a',attrs={'class':'elementor-post-info__terms-list-item'}).text.strip()
        try:
            category = constants.DAILYNEWS_CATEGORY_MAPPER[category]
            sub_category = soup.find('span', attrs={'class': 'elementor-post-info__terms-list'})
            sub_category = sub_category.find_all('a')
            sub_category = list(map(lambda s: s.text.strip(), sub_category))
            sub_category = sub_category[1:]
            for i in range(len(sub_category)):
                try:
                    sub_category[i] = category = constants.DAILYNEWS_CATEGORY_MAPPER[sub_category[i]]
                except:
                    logging.info(f'Error mapping {sub_category[i]}')
                    sub_category[i] = sub_category[i]
                    # continue
            if category in sub_category:
                sub_category.remove(category)
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
                             source='DAILYNEWS',
                             link=url,
                             category=category,
                             tags=tags,
                             sub_category = sub_category
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
