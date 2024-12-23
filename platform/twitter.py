from . import BasePlatform
from typing import List
from misc import TSBMessage

class Twitter(BasePlatform):
    def gather_messages(self, since_message_id: str) -> List[TSBMessage]:
        pass

    def reply(self, timestamps: str, platform_message_id: str) -> None:
        pass