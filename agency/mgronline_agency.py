import asyncio
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


class MgronlineAgency(Agency):
    def __init__(self, config):
        self.config = config

    def parse_date(self, date_text) -> datetime:
        date_text = ' '.join(date_text.strip().split(' '))
        date_text = date_text.replace('/', ' ')
        date_text = date_text.replace(':', '.')
        date_text = date_text.replace('\t', '')
        _, thai_month, thai_year, *_ = date_text.split(' ')
        date_text = date_text.replace(
            thai_month, constants.TH_FULL_MONTHS_MAPPER_MGR[thai_month])
        date_text = date_text.replace(thai_year, str(int(thai_year) - 543))
        date = datetime.strptime(date_text, r'%d %B %Y %H.%M')
        return date

    def parse_date_index(self, date_text) -> datetime:

        date_text = ' '.join(date_text.strip().split(' '))
        date_text = date_text.replace('/', ' ')
        date_text = date_text.replace(':', '.')
        date = datetime.strptime(date_text, r'%Y %m %d %H.%M.%S')
        return date
    
    def deleteHTML(self, inp: str) -> str:
        ls = []
        inp = list(inp)
        found = False
        isScript = False
        for i in range(len(inp)):
            if inp[i] == '<' and not found:
                if ''.join(inp[i + 1: i + 7]) == 'script':
                    isScript = True
                found = True
            elif inp[i] == '>' and found and not isScript:
                found = False
            elif inp[i] == '>' and found and isScript:
                isScript = False
            if not found and inp[i] != '>':
                ls.append(inp[i])
        return ''.join(ls)
        
    async def scrap_links(self, index_url, from_date, to_date, max_news):

        all_links = set()
        for page_number in range(0, (max_news//constants.NEWS_MAX_NUM_PER_PAGE)+1):
            soup = await self.scrap_html(index_url+'start='+str(page_number*10))
            if soup is None:
                logging.error(
                    f'failed to obtain {index_url} with page {page_number}')
                continue
            try:
                logging.info(f'page {page_number}')
                articles = soup.find_all('a',attrs={'class':'link'}, href=True)
                date_texts = soup.find_all('time', attrs={'class':'p-date-time-item'})
                date_texts = list(map(lambda date_text: date_text['data-pdatatimedata'], date_texts))
                dates = list(map(lambda date_text: self.parse_date_index(date_text), date_texts))
                min_date = min(dates)
                max_date = max(dates)
                links = list(map(lambda link: f'{link["href"]}', articles))
            except:
                continue
            
            for date, link in zip(dates, links):
                if soup.find_all('time', attrs={'class':'p-date-time-item'}) is not None and soup.find_all('a',attrs={'class':'link'}, href=True) is not None:
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

        if soup.find('div', attrs={'class': 'col-sm-7 col-md-8'}) is None:
            logging.error(f'failed info page')
            return
        soup_news = soup.find('div', attrs={'class': 'col-sm-7 col-md-8'})
        title = soup_news.find('header', attrs={'class': 'header-article'})
        title = soup_news.find('h1').text.strip()
        date_text = soup_news.find('time').text.strip()
        date = self.parse_date(date_text)
        try:
            content = soup.find('div', attrs={'class': 'article-content'})
            content = content.find('div', attrs={'class': 'detail m-c-font-article'})
            content = str(content).replace('<br/>', '\n')
            content = self.deleteHTML(content).split('\n')
            content = list(map(lambda a: a.strip(), content))
            while '' in content:
                content.remove('')
            content = '\n'.join(content)
        except:
            logging.info(f'error : content')
            
        category = url.split("/")[3]
        tags = soup.find('meta', attrs={'name': 'keywords'})
        tags = f'{tags["content"]}'.split(',')
        try:
            category = constants.MANGERONLINE_CATEGORY_MAPPER[category]
            sub_category = soup.find('div', attrs={'class': 'breadcrumb-container'})
            sub_category = sub_category.find_all('li')
            sub_category = list(map(lambda s: s.text.strip(), sub_category))
            sub_category = sub_category[2:]
            sub_category = ','.join(sub_category)
            for item in constants.MANAGER_DELETE_TAGS:
                tags.remove(item)
                tags = ','.join(tags)
        except:
            tags = ','.join(tags)
            logging.info(f'normal-tags: {tags}')
        finally:
            logging.info(f'{category}')
            if sub_category == '':
                sub_category = None
            logging.info(f'{sub_category}')
            logging.info(f'{tags}')

        return RawNewsEntity(publish_date=date,
                             title=title,
                             content=content,
                             created_at=datetime.now(),
                             source='MANAGERONLINE',
                             link=url,
                             category=category,
                             tags=tags,
                             sub_category=sub_category
                             )    
        
    async def scrap(self) -> List[RawNewsEntity]:
        index_urls = self.config['indexes_mgronline']
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
