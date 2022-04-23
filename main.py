import asyncio
from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from config import config
from scrapper import scrap_dailynews, scrap_mgronline, scrap_matichon, scrap_bkkbiznews, scrap_posttoday, scrap_the_standard, \
                     scrap_prachachat, scrap_posttoday

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
#matichon
trigger_configs = config['agency']['matichon']['scheduler']
for trigger_config in trigger_configs:
    scheduler.add_job(scrap_matichon,
                      trigger=CronTrigger(**trigger_config))
#bkkbiznews
trigger_configs = config['agency']['bkkbiznews']['scheduler']
for trigger_config in trigger_configs:
    scheduler.add_job(scrap_bkkbiznews,
                      trigger=CronTrigger(**trigger_config))
#the_standard
trigger_configs = config['agency']['the_standard']['scheduler']
for trigger_config in trigger_configs:
    scheduler.add_job(scrap_the_standard,
                      trigger=CronTrigger(**trigger_config))
# # prachachat
# trigger_configs = config['agency']['prachachat']['scheduler']
# for trigger_config in trigger_configs:
#     scheduler.add_job(scrap_prachachat,
#                       trigger=CronTrigger(**trigger_config))
#posttoday
trigger_configs = config['agency']['posttoday']['scheduler']
for trigger_config in trigger_configs:
    scheduler.add_job(scrap_posttoday,
                      trigger=CronTrigger(**trigger_config))

scheduler.start()
asyncio.get_event_loop().run_forever()
