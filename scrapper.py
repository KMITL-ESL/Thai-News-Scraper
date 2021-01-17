import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from agency import DailynewsAgency
from database import db

logging.basicConfig(level=logging.INFO)

async def scrap(agency, link):
    raw_news_entity = await agency.call(link)
    logging.info(raw_news_entity)
    try:
        db.add(raw_news_entity)
        db.commit()
    except IntegrityError:
        db.rollback()
        logging.info(f'Duplicated {raw_news_entity.link}')
async def main():
    index_url = 'https://www.dailynews.co.th/economic'
    agency = DailynewsAgency()
    links = await agency.scrap_links(index_url,
                                     from_date=datetime.now() - timedelta(days=1),
                                     to_date=datetime.now(),
                                     max_news=1000)

    logging.info(f'number of link = {len(links)}')
    await asyncio.gather(*[scrap(agency, link) for link in links])

asyncio.run(main())
