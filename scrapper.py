import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

<<<<<<< Updated upstream
from agency import DailynewsAgency
from database import db
=======
from agency import DailynewsAgency, ManagerOnlineAgency
from model import RawNewsEntity
from database import db
from config import config
import adapter

dailynews_agency = DailynewsAgency(config=config['agency']['dailynews'])
manageronline_agency = ManagerOnlineAgency(config=config['agency']['manageronline'])
>>>>>>> Stashed changes

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
<<<<<<< Updated upstream
async def main():
    index_url = 'https://www.dailynews.co.th/economic'
    agency = DailynewsAgency()
    links = await agency.scrap_links(index_url,
                                     from_date=datetime.now() - timedelta(days=1),
                                     to_date=datetime.now(),
                                     max_news=1000)
=======
    except Exception as err :
        db.rollback()
        logging.error(f'failed to store raw_news_entity')
        logging.error(err)


async def scrap_dailynews():
    # await adapter.publish_drop_table()
    raw_news_entities = await dailynews_agency.scrap()
    for entity in raw_news_entities:
        insert_raw_news(entity)
        post_news_response = await adapter.publish_raw_news(entity)
        logging.info(post_news_response)

async def scrap_manageronline():
    # await adapter.publish_drop_table()
    raw_news_entities = await manageronline_agency.scrap()
    for entity in raw_news_entities:
        insert_raw_news(entity)
        post_news_response = await adapter.publish_raw_news(entity)
        logging.info(post_news_response)

async def main():
    await scrap_dailynews()
    await scrap_manageronline()
>>>>>>> Stashed changes

    logging.info(f'number of link = {len(links)}')
    await asyncio.gather(*[scrap(agency, link) for link in links])

asyncio.run(main())
