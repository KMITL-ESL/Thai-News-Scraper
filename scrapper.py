import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from agency import DailynewsAgency, MgronlineAgency, MatichonAgency, BkkbiznewsAgency, TheStandardAgency
from model import RawNewsEntity
from database import db
from config import config
import adapter

dailynews_agency = DailynewsAgency(config=config['agency']['dailynews'])
mgronline_agency = MgronlineAgency(config=config['agency']['mgronline'])
matichon_agency = MatichonAgency(config=config['agency']['matichon'])
bkkbiznews_agency = BkkbiznewsAgency(config=config['agency']['bkkbiznews'])
the_standard_agency = TheStandardAgency(config=config['agency']['the_standard'])

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

async def scrap_matichon():
    # await adapter.publish_drop_table()
    raw_news_entities = await matichon_agency.scrap()
    for entity in raw_news_entities:
        insert_raw_news(entity)
        post_news_response = await adapter.publish_raw_news(entity)
        logging.info(post_news_response)

async def scrap_bkkbiznews():
    # await adapter.publish_drop_table()
    raw_news_entities = await bkkbiznews_agency.scrap()
    for entity in raw_news_entities:
        insert_raw_news(entity)
        post_news_response = await adapter.publish_raw_news(entity)
        logging.info(post_news_response)

async def scrap_the_standard():
    # await adapter.publish_drop_table()
    raw_news_entities = await the_standard_agency.scrap()
    for entity in raw_news_entities:
        insert_raw_news(entity)
        post_news_response = await adapter.publish_raw_news(entity)
        logging.info(post_news_response)

async def main():
    await scrap_dailynews()
    await scrap_mgronline()
    await scrap_matichon()
    await scrap_bkkbiznews()
    await scrap_the_standard()


if __name__ == '__main__':
    asyncio.run(main())
