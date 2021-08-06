import asyncio
import orjson as json

import aiohttp

from config import config
from model import RawNewsEntity

outbound_config = config['outbound']

async def publish_raw_news(entity: RawNewsEntity):
    url = outbound_config['post_news']
    async with aiohttp.ClientSession() as session:
        request_body = {
            'raw_news_id': entity.id,
            'title': entity.title,
            'content': entity.content,
            'publish_date': entity.publish_date,
            'source': entity.source,
            'link': entity.link,
            'category' : entity.category
        }
        async with session.post(url, data=json.dumps(request_body)) as res:
            return await res.json()
async def publish_drop_table():
    url = outbound_config['drop_news']
    async with aiohttp.ClientSession() as session:
        async with session.delete(url) as res:
            return await res.json()