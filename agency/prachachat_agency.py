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


class PrachachatAgency(Agency):
    def __init__(self, config):
        self.config = config

    def parse_date(self, date_text) -> datetime:
        date_text = date_text.replace(' +0000', '')
        date = datetime.strptime(date_text, r'%a, %d %b %Y %H:%M:%S')
        return date

    async def scrap_links(self, index_url, from_date, to_date, max_news):
        all_links = set()
        soup = await self.scrap_html(index_url)
        if soup is None:
            logging.error(
                f'failed to obtain {index_url}')
        print(f'scrap_links : {index_url}')
        print(soup.text)
        try: 
            articles = soup.find_all('item')
            print(articles)
            for item in articles:
                dic = dict()
                #publish_date
                dic['publish_date'] = self.parse_date(item.find('pubDate').text)
                #title
                dic['title'] = item.find('title').text
                #content
                content = item.find('content:encoded')
                content = content.find_all('p')[:-1]
                content = list(map(lambda a: a.text, content))
                content = ''.join(content)
                dic['content'] = content
                #link
                dic['link'] = item.find('link').text
                #category
                category = index_url.strip('/')[-2]
                try:
                    category = constants.PRACHACHAT_CATEGORY_MAPPER[category]
                except:
                    continue
                dic['category'] = category
                #tags
                soup2 = await self.scrap_html(dic['link'])
                tags = soup2.find('div', attrs={'class': 'td-post-source-tags'})
                tags = tags.find_all('a')
                tags = list(map(lambda a: a.text, tags))
                tags = ','.join(tags)
                dic['tags'] = tags
                #sub_category
                sub_category = item.find_all('category')
                sub_category = list(map(lambda a: a.text, sub_category))
                if category in sub_category:
                    sub_category.remove(category)
                dic['sub_category'] = sub_category
                #result
                all_links.add(dic)
                logging.info(dic)
        except:
            logging.error(f'failed to obtain {index_url}')
        
        return all_links

    async def call(self, url) -> RawNewsEntity:
        return RawNewsEntity(publish_date=url['publish_date'],
                             title=url['title'],
                             content=url['content'],
                             created_at=datetime.now(),
                             source='PRACHACHAT',
                             link=url['link'],
                             category=url['category'],
                             tags=url['tags'],
                             sub_category=url['sub_category']
                             )

    async def scrap(self) -> List[RawNewsEntity]:
        index_urls = self.config['indexes_prachachat']
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
