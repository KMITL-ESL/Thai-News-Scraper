import asyncio
import logging
from datetime import datetime, timedelta

from sqlalchemy.exc import IntegrityError

from agency import DailynewsAgency, MgronlineAgency, MatichonAgency, BkkbiznewsAgency, \
                   TheStandardAgency, PrachachatAgency, PostTodayAgency
from model import RawNewsEntity, MatichonRawNewsEntity
from database import db
from config import config
import adapter

dailynews_agency = DailynewsAgency(config=config['agency']['dailynews'])
mgronline_agency = MgronlineAgency(config=config['agency']['mgronline'])
matichon_agency = MatichonAgency(config=config['agency']['matichon'])
bkkbiznews_agency = BkkbiznewsAgency(config=config['agency']['bkkbiznews'])
the_standard_agency = TheStandardAgency(config=config['agency']['the_standard'])
prachachat_agency = PrachachatAgency(config=config['agency']['prachachat'])
posttoday_agency = PostTodayAgency(config=config['agency']['posttoday'])

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

def insert_matichon_raw_news(matichon_raw_news_entity: MatichonRawNewsEntity):
    if matichon_raw_news_entity is None:
        logging.error(f'failed to create matichon_raw_news_entity')
        return
    # logging.info(matichon_raw_news_entity)
    try:
        db.add(matichon_raw_news_entity)
        db.commit()
    except IntegrityError:
        db.rollback()
        logging.info(f'Duplicated {matichon_raw_news_entity.link}')
    except Exception as err :
        db.rollback()
        logging.error(f'failed to store matichon_raw_news_entity')
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
    matichon_raw_news_entities = await matichon_agency.scrap()
    for entity in matichon_raw_news_entities:
        insert_matichon_raw_news(entity)
        # post_news_response = await adapter.publish_matichon_raw_news(entity)
        logging.info(entity)

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

async def scrap_prachachat():
    # await adapter.publish_drop_table()
    raw_news_entities = await prachachat_agency.scrap()
    for entity in raw_news_entities:
        insert_raw_news(entity)
        post_news_response = await adapter.publish_raw_news(entity)
        logging.info(post_news_response)

async def scrap_posttoday():
    # await adapter.publish_drop_table()
    raw_news_entities = await posttoday_agency.scrap()
    for entity in raw_news_entities:
        insert_raw_news(entity)
        post_news_response = await adapter.publish_raw_news(entity)
        logging.info(post_news_response)

async def main():
    await scrap_dailynews()
    await scrap_mgronline()
    await scrap_matichon()
    # await scrap_bkkbiznews()
    await scrap_the_standard()
    # await scrap_prachachat()
    # await scrap_posttoday()

if __name__ == '__main__':
    asyncio.run(main())
