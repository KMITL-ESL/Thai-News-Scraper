import logging
import uuid
from datetime import datetime
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from model import RawNewsEntity
from util import constants

from agency import Agency


class DailynewsAgency(Agency):

    def parse_date(self, date_text) -> datetime:

        # Trim date name and น.
        date_text = ' '.join(date_text.strip().split(' ')[1:-1])
        date_text = date_text.replace('เวลา', '')  # remove เวลา
        date_text = date_text.replace('  ', ' ')
        _, thai_month, thai_year, *_ = date_text.split(' ')
        date_text = date_text.replace(
            thai_month, constants.TH_FULL_MONTHS_MAPPER[thai_month])
        date_text = date_text.replace(thai_year, str(int(thai_year) - 543))
        date = datetime.strptime(date_text, r'%d %B %Y %H.%M')
        return date

    async def call(self, url) -> RawNewsEntity:
        soup = await self.scrap_html(url)

        logging.info(url)
        title = soup.find('h1', attrs={'class': 'title'}).text.strip()
        date_text = soup.find('span', attrs={'class': 'date'}).text.strip()
        date = self.parse_date(date_text)
        logging.info(date)
        content = soup.find('div', attrs={'class': 'content-all'}).text.strip()
        tags = soup.find('ol', attrs={'class': 'breadcrumb'}).find_all('li')
        category = tags[-1].text.strip()
        return RawNewsEntity(id=str(uuid.uuid4()),
                             publish_date=date,
                             title=title,
                             content=content,
                             created_at=datetime.now(),
                             source='DAILYNEWS',
                             link=url
                             )

    async def scrap_links(self, index_url, from_date, to_date, max_news):
        root_url = urlparse(index_url).hostname
        topic = index_url.split('/')[-1]

        page_number = 1
        all_links = set()
        while len(all_links) < max_news:

            soup = await self.scrap_html(index_url, params={'page': page_number})
            logging.info(f'page {page_number}')
            articles = soup.find_all('a', attrs={'class': 'media'}, href=True)
            # filter article only the article that contains date
            articles = list(filter(lambda article: article.find(
                'span', attrs={'class': 'media-date'}) is not None, articles))

            date_texts = list(map(lambda article: article.find(
                'span', attrs={'class': 'media-date'}).text, articles))
            dates = list(
                map(lambda date_text: self.parse_date(date_text), date_texts))

            min_date = min(dates)
            max_date = max(dates)

            links = list(
                map(lambda link: f'https://{root_url}{link["href"]}', articles))
            for date, link in zip(dates, links):
                all_links.add(link)
                logging.info(link)
            if min_date < from_date:
                break

            page_number += 1
        return all_links
