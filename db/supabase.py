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
            url, key, options=ClientOptions(auto_refresh_token=True, persist_session=True)
        )
        return cls(supabase_client)

    async def get_latest_message_id(self) -> Optional[str]:
        logging.debug("get_latest_message_id")
        response = await self.supabase.table("JobRun").select("newest_msg_id").neq("newest_msg_id", None).order("id", desc=True).limit(1).execute()
        logging.info(response)
        if not response.data:
            return None
        return response.data[0]["newest_msg_id"]
    
    async def insert_jobrun(self, messages: List[TSBMessage]) -> None:
        logging.debug("insert_jobrun")
        newest_msg_id = max([int(z.msg_id) for z in messages], default=None)
        data = {"nr_msgs_found":len(messages), "newest_msg_id": newest_msg_id}
        response = await self.supabase.table("JobRun").insert(data).execute()
        logging.info(response)

    async def insert_message(self, message: TSBMessage) -> None:
        logging.debug("insert_message")
        response = await self.supabase.table("TSBMessage").insert({k: v for k, v in vars(message).items() if k != "id"}).execute()
        logging.info(response)

    async def get_messages_to_process(self, limit: Optional[int]) -> List[TSBMessage]:
        logging.debug("get_messages_to_process")
        query = self.supabase.table("TSBMessage").select("*").eq("status", 0).order("id")
        if limit:
            query = query.limit(limit)
        response = await query.execute()
        logging.info(response)
        if not response.data:
            return []
        return [TSBMessage(id=m["id"], status=m["status"], msg_text=m["msg_text"], msg_from=m["msg_from"], msg_id=m["msg_id"]) for m in response.data]

    async def get_timestamps(self, video_id: str) -> Optional[str]:
        logging.debug("get_timestamps")
        response = await self.supabase.table("Chapter").select("timestamps").eq("video_id", video_id).limit(1).execute()
        logging.info(response)
        if not response.data:
            return None
        return response.data[0]["timestamps"]

    async def update(self, message: TSBMessage, status: Status) -> None:
        logging.debug("update")
        response = await self.supabase.table("TSBMessage").update({"status": status.value}).eq("id", message.id).execute()
        logging.info(response)
    
    async def add_chapters(self, video_id: str, timestamps: str) -> None:
        logging.debug("add_chapters")
        response = await self.supabase.table("Chapter").insert({"video_id": video_id, "timestamps": timestamps}).execute()
        logging.info(response)
