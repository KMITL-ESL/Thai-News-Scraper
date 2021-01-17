import asyncio
from datetime import datetime, timedelta
from agency import DailynewsAgency
import logging
logging.basicConfig(level=logging.INFO)

async def main():
    index_url = 'https://www.dailynews.co.th/economic'
    agency = DailynewsAgency()
    links = await agency.scrap_links(index_url,
                                     from_date=datetime.now() - timedelta(days=7),
                                     to_date=datetime.now(),
                                     max_news=1000)

    logging.info(f'number of link = {len(links)}')
    await asyncio.gather(*[agency.call(link) for link in links])

asyncio.run(main())
