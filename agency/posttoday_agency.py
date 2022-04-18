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


class PostTodayAgency(Agency):
    def __init__(self, config):
        self.config = config

    def parse_date(self, date_text) -> datetime:
        date_text = date_text.replace(' +0700', '')
        date = datetime.strptime(date_text, r'%a, %d %b %Y %H:%M:%S')
        return date

    def scrap_date(self, d: str) -> str:
        ls = []
        inp = list(d)
        found = False
        isLink = False
        for i in range(len(d)):
            if inp[i] == '<' and not found:
                if ''.join(d[i + 1: i + 6]) == 'link/':
                    isLink = True
                found = True
            elif d[i] == '>' and found and not isLink:
                found = False
            elif d[i] == '>' and found and isLink:
                isLink = False
            if not found and d[i] != '>':
                ls.append(d[i])
        return ''.join(ls)

    async def scrap_links(self, index_url, from_date, to_date, max_news):

        all_links = set()
        soup = await self.scrap_html(index_url)
        if soup is None:
            logging.error(f'failed to obtain {index_url}')
        print(soup)
        try: 
            articles = soup.find_all('item')
            for item in articles:
                print(item)
                dic = dict()
                #publish_date
                dic['publish_date'] = self.parse_date(item.find('pubdate').text)
                #title
                dic['title'] = item.find('title').text
                #link
                _link = self.scrap_date(item)
                dic['link'] = _link
                print(f'\n data : {dic} \n')
                #category
                soup2 = await self.scrap_html(dic['link'])
                pre_category = soup2.find('nav', attrs={'class': 'breadcrumb'})
                pre_category = pre_category.find_all('li')[0:]
                pre_category = list(map(lambda a: a.text, pre_category))
                category = pre_category[0]
                dic['category'] = category
                #tags
                tags = soup2.find('div', attrs={'class': 'box-tag'})
                tags = tags.find_all('a')
                tags = list(map(lambda a: a.text, tags))
                tags = ','.join(tags)
                dic['tags'] = tags
                #content
                content = soup2.find('div', attrs={'class': 'article-content'})
                content = content.find_all('p')
                content = list(map(lambda a: a.text, content))
                content = '\n'.join(content)
                while '\n\n' in content:
                    category = category.replace('\n\n', '\n')
                dic['content'] = content
                #sub_category
                sub_category = pre_category[0:]
                if category in sub_category:
                    sub_category.remove(category)
                sub_category = ','.join(sub_category)
                dic['sub_category'] = sub_category
                #result
                all_links.add(dic)
                logging.info(dic)
        except:
            logging.info(f'failed to obtain {index_url}')
            pass
        
        return all_links

    async def call(self, url) -> RawNewsEntity:

        return RawNewsEntity(publish_date=url['publish_date'],
                             title=url['title'],
                             content=url['content'],
                             created_at=datetime.now(),
                             source='POSTTODAY',
                             link=url['link'],
                             category=url['category'],
                             tags=url['tags'],
                             sub_category=url['sub_category']
                             )

    async def scrap(self) -> List[RawNewsEntity]:
        index_urls = self.config['indexes_posttoday']
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