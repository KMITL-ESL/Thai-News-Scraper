import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import config
from scrapper import scrap_dailynews, scrap_manageronline

scheduler = AsyncIOScheduler()

# dailynews
trigger_configs = config['agency']['dailynews']['scheduler']
for trigger_config in trigger_configs:
    scheduler.add_job(scrap_dailynews,
                      trigger=CronTrigger(**trigger_config))

# manageronline
#trigger_configs = config['agency']['manageronline']['scheduler']
#for trigger_config in trigger_configs:
#    scheduler.add_job(scrap_manageronline,
 #                     trigger=CronTrigger(**trigger_config))

scheduler.start()
asyncio.get_event_loop().run_forever()
