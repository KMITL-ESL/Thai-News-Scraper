import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from agency import DailynewsAgency, MgronlineAgency
from model import RawNewsEntity
from database import db
from config import config
import adapter

dailynews_agency = DailynewsAgency(config=config['agency']['dailynews'])
mgronline_agency = MgronlineAgency(config=config['agency']['mgronline'])

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

async def scrap_mgronline():
    # await adapter.publish_drop_table()
    raw_news_entities = await mgronline_agency.scrap()
    for entity in raw_news_entities:
        insert_raw_news(entity)
        post_news_response = await adapter.publish_raw_news(entity)
        logging.info(post_news_response)

async def main():
    await scrap_dailynews()
    await scrap_mgronline()


if __name__ == '__main__':
    asyncio.run(main())
