import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from agency import DailynewsAgency, ManagerAgency
from model import RawNewsEntity
from database import db
from config import config

dailynews_agency = DailynewsAgency(config=config['agency']['dailynews'])
manager_agency = ManagerAgency(config=config['agency']['manageronline'])

logging.basicConfig(level=logging.INFO)


def insert_raw_news(raw_news_entity: RawNewsEntity):
    if raw_news_entity is None:
        logging.error(f'failed to create raw_news_entity')
        return
    logging.info(raw_news_entity)
    try:
        db.add(raw_news_entity)
        db.commit()
    except IntegrityError:
        db.rollback()
        logging.info(f'Duplicated {raw_news_entity.link}')
    except Exception as err :
        logging.error(f'failed to store raw_news_entity')
        logging.error(err)


async def scrap_dailynews():
    raw_news_entities = await dailynews_agency.scrap()
    for entity in raw_news_entities:
        insert_raw_news(entity)


async def main():
    # await scrap_dailynews()
    # print(await manager_agency.scrap_links('https://mgronline.com/motoring'))

    entities = await manager_agency.scrap()

    print(entities)
    # print(await manager_agency.call('https://mgronline.com/motoring/detail/9610000104126'))


if __name__ == '__main__':
    asyncio.run(main())
