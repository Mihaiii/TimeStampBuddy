from . import BaseDB
from typing import Optional, List
from misc import TSBMessage, Status

class Supabase(BaseDB):
    def get_latest_message_id(self) -> Optional[str]:
        pass

    def insert_messages(self, messages: List[TSBMessage]) -> None:
        pass

    def get_messages_to_process(self, top: Optional[int]) -> Optional[TSBMessage]:
        pass

    def get_timestamps(self, message: TSBMessage) -> Optional[str]:
        pass

    def update(self, message: TSBMessage, status: Status) -> None:
        pass