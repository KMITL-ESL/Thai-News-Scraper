import asyncio
import logging
import uuid
from datetime import datetime, timedelta
from typing import List
from urllib.parse import urlparse, urljoin

import requests
from bs4 import BeautifulSoup
from config import config
from model import RawNewsEntity
from util import constants

from agency import Agency


class ManagerOnlineAgency(Agency):
    def __init__(self, config):
        self.config = config

    def parse_date_index(self, date_text) -> datetime:
        
        date = datetime.strptime(date_text, r'%Y/%m/%d %H:%M:%S')
        return date

    def parse_date(self, date_text) -> datetime:
        
        _, thai_month, thai_year, *_ = date_text.split(' ')
        date_text = date_text.replace(
            thai_month, constants.TH_MONTHS_MAPPER[thai_month])
        date_text = date_text.replace(thai_year, str(int(thai_year) - 543))
        date = datetime.strptime(date_text, r'%d %B %Y %H:%M')
        return date

    async def call(self, url, category) -> RawNewsEntity:
        logging.info("url")
        soup = await self.scrap_html(url)

        logging.info(url)
        title = soup.find('header', attrs={'class': 'header-article'})
        title = title.find('h1').text

        date_text = soup.find_all('time')
        date_text = date_text[0].text
        date = self.parse_date(date_text)        
        logging.info(date)

        content = soup.find('div', attrs={'class': 'm-detail-container'}).text.strip()
        tags = soup.find('ul', attrs={'class': 'pm-tags'}).find_all('li')
        tags = list(map(lambda tag: tag.find('a', href=True).text, tags))

        return RawNewsEntity(id=str(uuid.uuid4()),
                             publish_date=date,
                             title=title,
                             content=content,
                             created_at=datetime.now(),
                             source='MANAGERONLINE',
                             link=url,
                             )

    async def scrap_links(self, index_url, from_date, to_date, max_news):        
        page_number = 0
        all_links = set()
        all_topic_links = set()
                                
        soup = await self.scrap_html(index_url)
        topic_links = soup.find_all('div', attrs={'class': 'c-nav-menu'})
        topic_links = topic_links[0]
        
        topic_links = topic_links.find_all('a',  href=True)
        topic_links = topic_links[:-1]
        topic_links = list(map(lambda link: f'{link["href"]}', topic_links))
        
        while len(topic_links) > 0 :
            link = topic_links.pop()
            link_element = link.split('/')
            chk_index_page = link_element[-1].find('start=')
            if chk_index_page > -1 :
                all_topic_links.add(link)
            else :
                subsoup = await self.scrap_html(link)
                sublinks = subsoup.find_all('div', attrs={'class': 'c-nav-menu'})
                sublinks = sublinks[0]
                sublinks = sublinks.find_all('a',  href=True)
                sublinks = sublinks[:-1]
                sublinks = list(map(lambda link: f'{link["href"]}', sublinks))
                topic_links.extend(sublinks)
        logging.info(all_topic_links)
        
        for topic_url in all_topic_links :         
            num_link_before = len(all_links)
            while len(all_links) < max_news:  
                topic_url = urljoin(topic_url,'start='+str(page_number))
                soup = await self.scrap_html(topic_url)                
                articles = soup.find_all('a', attrs={'class': 'link'}, href=True)
                if not articles:
                    break

                date_raw = soup.find_all('time', attrs={'class': 'p-date-time-item'})
                date_texts = list(map(lambda date_text: date_text['data-pdatatimedata'], date_raw))

                dates = list(map(lambda date_text: self.parse_date_index(date_text), date_texts))

                min_date = min(dates)
                max_date = max(dates)

                links = list(map(lambda link: f'{link["href"]}', articles))
                for date, link in zip(dates, links):                
                    if date < from_date or date > to_date:         
                        break
                    else:
                        all_links.add(link)

                num_link_present = len(all_links)
                if num_link_present > num_link_before:
                    num_link_before = len(all_links)
                    page_number += 10
                else :
                    break
            
            page_number = 0
        logging.info(all_links)
        
        return all_links

    def scrap_category(self, index_url):
        topic = index_url.split('/')[-1]        
        return topic

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
