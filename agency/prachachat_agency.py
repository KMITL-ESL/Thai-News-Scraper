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


class PrachachatAgency(Agency):
    def __init__(self, config):
        self.config = config
        
    async def scrap_links(self, index_url, from_date, to_date, max_news):

        all_links = set()
        for page_number in range(0, (max_news//constants.NEWS_MAX_NUM_PER_PAGE)+1):
            soup = await self.scrap_html(index_url+'page/'+str(page_number))
            if soup is None:
                logging.error(
                    f'failed to obtain {index_url} with page {page_number}')
                continue
            try:
                logging.info(f'page {page_number}')
                soup = soup.find('div', attrs={'class':'td-ss-main-content'})
                print(soup)
                articles = soup.find_all('a',attrs={'class':'link'}, href=True)
                links = list(map(lambda link: f'{link["href"]}', articles))
            except:
                continue
            
            for link in links:
                if link not in all_links:
                    all_links.add(link)
                    logging.info(link)
            
            dates = list()
            try:
                for link in all_links:
                    soup = await self.scrap_html(link)
                    if soup is None:
                        logging.error(
                            f'failed to obtain {link}')
                        continue
                    date_text = soup.find('time', attrs={'class':'entry-date updated td-module-date'}, datetime=True)
                    dates.append(datetime(date_text["datetime"])) 
            except:
                continue
            
            min_date = min(dates)
            if min_date < from_date:
                break
        return all_links

    async def call(self, url) -> RawNewsEntity:
        soup = await self.scrap_html(url)
        if soup is None:
            logging.error(f'failed to obtain {url}')
            return

        logging.info(f'scrap {url}')

        soup_news = soup.find('div', attrs={'class': 'td-ss-main-content'})
        title = soup_news.find('header', attrs={'class': 'td-post-title'})
        title = soup_news.find('h1', attrs={'class': 'entry-title'}).text.strip()
        date_text = soup_news.find('time', attrs={'class':'entry-date updated td-module-date'}, datetime=True)
        date = datetime(date_text["datetime"])
        try:
            content = soup_news.find('div', attrs={'itemprop': 'articleBody'})
            content = content.find_all('p')
            content = list(map(lambda p: p.text.strip(), content))
            while '' in content:
                content.remove('')
            content = '\n'.join(content)
        except:
            logging.info(f'error : content')
        
        category = url.split("/")[3]
        tags = soup.find('script', attrs={'class': 'yoast-schema-graph'}).text
        tags = dict(category)['keywords']
        try:
            sub_category = soup.find('div', attrs={'class': 'entry-crumbs'})
            sub_category = sub_category.find_all('span')
            sub_category = list(map(lambda s: s.text.strip(), sub_category))
            sub_category = sub_category[2:-1]
            sub_category = ','.join(sub_category)
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
                             source='PRACHACHAT',
                             link=url,
                             category=category,
                             tags=tags,
                             sub_category=sub_category
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
