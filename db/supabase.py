from . import BaseDB
from typing import Optional, List
from misc import TSBMessage, Status
import os
from supabase import create_client, Client
import logging
import json
from supabase.lib.client_options import ClientOptions

class Supabase(BaseDB):
    def __init__(self):
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        self.supabase = create_client(url, key, options=ClientOptions(auto_refresh_token=True))

    async def get_latest_message_id(self) -> Optional[str]:
        response = await supabase.table("JobRun").select("newest_msg_id").order("id", desc=True).limit(1).execute()
        logging.info(response)
        if response.error:
            raise Exception(json.dumps(response))
        if len(response) == 0:
            return None
        return response[0]["newest_msg_id"]
    
    async def insert_jobrun(self, messages: List[TSBMessage], headers: Dictionary[str, str]) -> None:
        newest_msg_id = max([int(z["msg_id"]) for z in messages])
        data = {"nr_msgs_found":len(messages), "newest_msg_id": newest_msg_id, "headers": json.dumps(headers)}
        response = await supabase.table("JobRun").insert(data).execute()
        logging.info(response)
        if response.error:
            raise Exception(json.dumps(response))

    async def insert_message(self, message: TSBMessage) -> None:
        response = await supabase.table("TSBMessage").insert({k: v for k, v in vars(message).items() if k != "id"}).execute()
        logging.info(response)
        if response.error:
            raise Exception(json.dumps(response))

    async def get_messages_to_process(self, limit: Optional[int]) -> Optional[TSBMessage]:'
        query = supabase.table("TSBMessage").select("*").eq("status", 0).order("id")
        if limit:
            query = query.limit(limit)
        response = await query.execute()
        logging.info(response)
        if response.error:
            raise Exception(json.dumps(response))
        if len(response) == 0:
            return None
        return response[0]["newest_msg_id"]

    async def get_timestamps(self, video_id: str) -> Optional[str]:
        response = await supabase.table("Chapter").select("summary").eq("video_id", video_id).limit(1).execute()
        logging.info(response)
        if response.error:
            raise Exception(json.dumps(response))
        if len(response) == 0:
            return None
        return response[0]["summary"]

    async def update(self, message: TSBMessage, status: Status) -> None:
        response = await supabase.table("countries").update({"status": status.value}).eq("id", message["id"]).execute()
        logging.info(response)
        if response.error:
            raise Exception(json.dumps(response))
