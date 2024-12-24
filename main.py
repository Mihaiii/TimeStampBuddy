import asyncio
import os
import logging
from typing import List
from db import BaseDB, Supabase
from msg_platform import BasePlatform, Twitter
from dotenv import load_dotenv
import traceback
from misc import Status, TSBMessage
import re

load_dotenv()
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
DEFAULT_CRON_INTERVAL_SEC = 60 * 15
DEFAULT_PROCESSOR_INTERVAL_SEC = 60 * 5
DEFAULT_MAX_PARALLEL_MESSAGES = 1

class CronProcessor:
    def __init__(self, db: BaseDB, platform: BasePlatform):
        self.db = db
        self.platform = platform

    async def add_platform_messages(self):
        while True:
            cron_interval = int(os.environ.get("CRON_INTERVAL", DEFAULT_CRON_INTERVAL_SEC))
            logging.info(f"Running cron job with interval {cron_interval} seconds...")
            try:
                latest_db_id = await self.db.get_latest_message_id()
                logging.debug(f"{latest_db_id=}")                
                messages = await self.platform.gather_messages(since_message_id=latest_db_id)
                logging.debug(f"{len(messages)=}")
                await self.db.insert_jobrun(messages)
                for msg in messages:
                    await self.db.insert_message(msg)
                logging.info("Cron job done!")
            except Exception as e:
                logging.error(f"Error in add_platform_messages. {traceback.format_exc()} {e}")
            await asyncio.sleep(cron_interval)

    async def run_data_processor(self):
        while True:
            processor_interval = int(os.environ.get("PROCESSOR_INTERVAL", DEFAULT_PROCESSOR_INTERVAL_SEC))
            max_parallel_messages = int(os.environ.get("MAX_MESSAGES", DEFAULT_MAX_PARALLEL_MESSAGES))
            messages = await self._get_messages_to_process(max_parallel_messages)
            if not messages:
                logging.info(f"No message to be processed found in the db")
                await asyncio.sleep(processor_interval)
                logging.info(f"Processing data with interval {processor_interval} seconds...")
                continue

            tasks = [self._process_message(msg) for msg in messages]
            await asyncio.gather(*tasks)

    async def _get_messages_to_process(self, limit: int) -> List:
        try:
            return await self.db.get_messages_to_process(limit)
        except Exception as e:
            logging.error(f"Error getting messages to process: {traceback.format_exc()} {e}")
            return []

    def _get_video_id(self, text):
        pattern = r'https?:\/\/(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/)|youtu\.be\/)([0-9A-Za-z_-]{11})'
        match = re.search(pattern, text)
        if match:
            return match.group(1)
        else:
            return None

    async def _process_message(self, msg: TSBMessage):
        try:
            await self.db.update(msg, Status.process_start)
        except Exception as e:
            logging.error(f"Error when updating to Processed. {msg.id=}. {traceback.format_exc()} {e}")


        video_id = self._get_video_id(msg.msg_text)
        if not video_id:
            try:
                await self.db.update(msg, Status.invalid)
            except Exception as e:
                logging.error(f"Error when updating to Invalid. {msg.id=}. {traceback.format_exc()} {e}")
            finally:
                return

        timestamps = await self.db.get_timestamps(video_id=video_id)
        if timestamps is None:
            # TODO: Call scripts to get timestamps, insert them into the database (Chapters), and assign them to timestamps
            pass

        try:
            await self.db.update(msg, Status.process_end)
        except Exception as e:
            logging.error(f"Error when updating to Processed. {msg.id=}. {traceback.format_exc()} {e}")

        try:
            await self.platform.reply(timestamps, msg.platform_message_id)
            await self.db.update(msg, Status.answered)
        except Exception as e:
            logging.error(f"Error when replying or when updating to Answered. {msg.id=}, {timestamps=}, {traceback.format_exc()} {e}")

        logging.info("Data processed!")

async def main():
    db = await Supabase.create()
    platform = Twitter()
    cron_processor = CronProcessor(db, platform)

    # I want 2 methods here and not just to pass the result of add_platform_messages to run_data_processor.
    # The reason is that I want the db to always reflect the current state because I'll make updates directly 
    # on it on supabase. And this will happen for multiple reasons, including that I expect my app to
    # crash from time to time and I'll manually update the status of a record to be reprocessed or
    # to not be considered again if I manually post the reply from the bot account via the UI.
    await asyncio.gather(
        cron_processor.add_platform_messages(),
        cron_processor.run_data_processor()
    )

if __name__ == "__main__":
    asyncio.run(main())
