from abc import ABC, abstractmethod
from typing import List, Tuple, Dict
from misc import TSBMessage


class BasePlatform(ABC):

    @abstractmethod
    async def get_original_url(self, message_text: str) -> str:
        # Some platforms don't allow external links to be posted directly
        # and use an internal service to redirect to the original URL
        pass

    @abstractmethod
    async def gather_messages(self, since_message_id: str) -> List[TSBMessage]:
        # Get latest messages that mention a particular user
        # and are newer than the message id of since_message_id
        pass

    @abstractmethod
    async def reply(self, text: str, platform_message_id: str) -> None:
        # Reply to a message with the id = platform_message_id
        pass
