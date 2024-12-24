from . import BaseDB
from typing import Optional, List, Dict
from misc import TSBMessage, Status
import os
import logging
from supabase.lib.client_options import ClientOptions
from supabase import create_async_client

class Supabase(BaseDB):
    def __init__(self, supabase_client):
        self.supabase = supabase_client

    @classmethod
    async def create(cls):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        supabase_client = await create_async_client(
            url, key, options=ClientOptions(auto_refresh_token=True)
        )
        return cls(supabase_client)

    async def get_latest_message_id(self) -> Optional[str]:
        logging.debug("get_latest_message_id")
        response = await self.supabase.table("JobRun").select("newest_msg_id").order("id", desc=True).limit(1).execute()
        logging.info(response)
        if len(response.data) == 0:
            return None
        return response.data[0]["newest_msg_id"]
    
    async def insert_jobrun(self, messages: List[TSBMessage]) -> None:
        logging.debug("insert_jobrun")
        newest_msg_id = max([int(z.msg_id) for z in messages])
        data = {"nr_msgs_found":len(messages), "newest_msg_id": newest_msg_id}
        response = await self.supabase.table("JobRun").insert(data).execute()
        logging.info(response)

    async def insert_message(self, message: TSBMessage) -> None:
        logging.debug("insert_message")
        response = await self.supabase.table("TSBMessage").insert({k: v for k, v in vars(message).items() if k != "id"}).execute()
        logging.info(response)

    async def get_messages_to_process(self, limit: Optional[int]) -> Optional[TSBMessage]:
        logging.debug("get_messages_to_process")
        query = self.supabase.table("TSBMessage").select("*").eq("status", 0).order("id")
        if limit:
            query = query.limit(limit)
        response = await query.execute()
        logging.info(response)
        if len(response.data) == 0:
            return None
        return response.data[0]["newest_msg_id"]

    async def get_timestamps(self, video_id: str) -> Optional[str]:
        response = await self.supabase.table("Chapter").select("summary").eq("video_id", video_id).limit(1).execute()
        logging.info(response)
        if len(response.data) == 0:
            return None
        return response.data[0]["summary"]

    async def update(self, message: TSBMessage, status: Status) -> None:
        response = await self.supabase.table("countries").update({"status": status.value}).eq("id", message["id"]).execute()
        logging.info(response)
