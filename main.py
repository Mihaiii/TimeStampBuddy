import asyncio
import os
import logging
from typing import List
from db import BaseDB, Supabase
from platform import BasePlatform, Twitter
from dotenv import load_dotenv


load_dotenv()
logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)
DEFAULT_CRON_INTERVAL_SEC = 60 * 15
DEFAULT_PROCESSOR_INTERVAL_SEC = 60 * 5
DEFAULT_MAX_PARALLEL_MESSAGES = 1

class CronProcessor:
    def __init__(self, db: BaseDB, platform: BasePlatform):
        self.db = db
        self.platform = platform

    async def run_cron_job(self):
        while True:
            cron_interval = int(os.environ.get("CRON_INTERVAL", DEFAULT_CRON_INTERVAL_SEC))
            logging.info(f"Running cron job with interval {cron_interval} seconds...")
            try:
                latest_db_id = await self.db.get_latest_message_id()
                logging.debug(f"{latest_db_id=}")                
                messages, headers = await self.platform.gather_messages(since_message_id=latest_db_id)
                logging.debug(f"{len(messages)=}")
                await self.db.insert_jobrun(messages, headers)
                for msg in messages:
                    await self.db.insert_message(msg)
                logging.info("Cron job done!")
            except Exception as e:
                logging.error(f"Error in run_cron_job. {e}")
            await asyncio.sleep(cron_interval)

    async def run_data_processor(self):
        while True:
            processor_interval = int(os.environ.get("PROCESSOR_INTERVAL", DEFAULT_PROCESSOR_INTERVAL_SEC))
            max_parallel_messages = int(os.environ.get("MAX_MESSAGES", DEFAULT_MAX_PARALLEL_MESSAGES))
            messages = await self._get_messages_to_process(max_parallel_messages)
            if not messages:
                await asyncio.sleep(processor_interval)
                logging.info(f"Processing data with interval {processor_interval} seconds...")
                continue

            tasks = [self._process_message(msg) for msg in messages]
            await asyncio.gather(*tasks)

    async def _get_messages_to_process(self, limit: int) -> List:
        try:
            return await self.db.get_messages_to_process(limit)
        except Exception as e:
            logging.error(f"Error getting messages to process: {e}")
            return []

    def _get_video_id(self, text):
        pattern = r'https?:\/\/(?:www\.)?(?:youtube\.com\/(?:watch\?v=|embed\/|v\/)|youtu\.be\/)([0-9A-Za-z_-]{11})'
        match = re.search(pattern, message)
        if match:
            return match.group(1)
        else:
            return None

    async def _process_message(self, msg):
        try:
            await self.db.update(msg, Status.process_start)
        except Exception as e:
            logging.error(f"Error when updating to Processed. {msg.id=}. {e}")


        video_id = self._get_video_id(msg["text"])
        if not video_id:
            try:
                await self.db.update(msg, Status.invalid)
            except Exception as e:
                logging.error(f"Error when updating to Invalid. {msg.id=}. {e}")

        timestamps = await self.db.get_timestamps(video_id=video_id)
        if timestamps is None:
            # TODO: Call scripts to get timestamps, insert them into the database (Chapters), and assign them to timestamps
            pass

        try:
            await self.db.update(msg, Status.process_end)
        except Exception as e:
            logging.error(f"Error when updating to Processed. {msg.id=}. {e}")

        try:
            await self.platform.reply(timestamps, msg.platform_message_id)
            await self.db.update(msg, Status.answered)
        except Exception as e:
            logging.error(f"Error when replying or when updating to Answered. {msg.id=}, {msg.platform_message_id=}, {timestamps=}, {e}")

        logging.info("Data processed!")

async def main():
    db = Supabase()
    platform = Twitter()
    cron_processor = CronProcessor(db, platform)

    await asyncio.gather(
        cron_processor.run_cron_job(),
        cron_processor.run_data_processor()
    )

if __name__ == "__main__":
    asyncio.run(main())
