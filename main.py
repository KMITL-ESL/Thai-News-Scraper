import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import config
from scrapper import scrap_dailynews, scrap_mgronline

scheduler = AsyncIOScheduler()

# dailynews
trigger_configs = config['agency']['dailynews']['scheduler']
for trigger_config in trigger_configs:
    scheduler.add_job(scrap_dailynews,
                      trigger=CronTrigger(**trigger_config))
# manager
trigger_configs = config['agency']['mgronline']['scheduler']
for trigger_config in trigger_configs:
    scheduler.add_job(scrap_mgronline,
                      trigger=CronTrigger(**trigger_config))

scheduler.start()
asyncio.get_event_loop().run_forever()
