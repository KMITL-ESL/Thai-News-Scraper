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

        all_details = set()
        soup = await self.scrap_html(index_url)
        if soup is None:
            logging.error(f'failed to obtain {index_url}')
        # print(soup)
        try: 
            articles = soup.find_all('item')
            for item in articles:
                # print(item)
                dic = dict()
                dic['publish_date'] = self.parse_date(item.find('pubdate').text) #publish_date
                dic['title'] = item.find('title').text #title
                prelink = str(item) #link
                start = False
                getLink = False
                link = []
                for j in range(len(prelink)):
                    if not getLink:
                        if not start:
                            if prelink[j] == '<' and prelink[j + 1] == 'l' and prelink[j + 2] == 'i':
                                start = True
                        else:
                            if prelink[j] == '>':
                                getLink = True
                    else:
                        if prelink[j] != '<':
                            link.append(prelink[j])
                        else:
                            break
                dic['link'] = ''.join(link)
                # print(dic)
                soup2 = await self.scrap_html(dic['link']) #category
                if soup2 is None:
                    continue
                pre_category = soup2.find('nav', attrs={'aria-label': 'breadcrumb'})
                pre_category = pre_category.find_all('li')[1:]
                pre_category = list(map(lambda a: a.text, pre_category))
                category = pre_category[0]
                dic['category'] = category
                tags = soup2.find('div', attrs={'class': 'box-tag'}) #tags
                if tags is not None:
                    tags = tags.find_all('a')
                    tags = list(map(lambda a: a.text, tags))
                    tags = ','.join(tags)
                dic['tags'] = tags
                content = soup2.find('div', attrs={'class': 'article-content'}) #content
                content = content.find_all('p')
                content = list(map(lambda a: a.text, content))
                content = '\n'.join(content)
                while '\n\n' in content:
                    content = content.replace('\n\n', '\n')
                dic['content'] = content
                sub_category = pre_category[0:] #sub_category
                if category in sub_category:
                    sub_category.remove(category)
                sub_category = ','.join(sub_category)
                dic['sub_category'] = sub_category
                all_details.add(tuple(dic.items())) #result
                # logging.info(all_details)
        except:
            logging.info(f'failed to obtain {index_url}')
            pass
        
        return all_details

    async def call(self, detail) -> RawNewsEntity:
        try:
            all_info = dict()
            all_info.update(info for info in detail)
        except:
            logging.info(f'failed to obtain func:call')

        return RawNewsEntity(publish_date=all_info['publish_date'],
                             title=all_info['title'],
                             content=all_info['content'],
                             created_at=datetime.now(),
                             source='POSTTODAY',
                             link=all_info['link'],
                             category=all_info['category'],
                             tags=all_info['tags'],
                             sub_category=all_info['sub_category']
                             )

    async def scrap(self) -> List[RawNewsEntity]:
        index_urls = self.config['indexes_posttoday']
        details = set()
        for index_url in index_urls:
            detail = await self.scrap_links(index_url,
                                            from_date=datetime.now() -
                                            timedelta(
                                                days=self.config['since_datedelta']),
                                            to_date=datetime.now(),
                                            max_news=self.config['max_news_per_batch'])
            details.update(detail)

        logging.info(f'number of detail = {len(details)}')
        entities = await asyncio.gather(*[self.call(detail) for detail in details])
        return list(filter(lambda entity: entity is not None, entities))