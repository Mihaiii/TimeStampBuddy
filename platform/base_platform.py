from abc import ABC, abstractmethod
from typing import List
from misc import TSBMessage


class BasePlatform(ABC):
    @abstractmethod
    def gather_messages(self, since_message_id: str) -> List[TSBMessage]:
        # Get latest messages that mention a particular user
        # and are newer than the message id of since_message_id
        pass

    @abstractmethod
    def reply(self, text: str, platform_message_id: str) -> None:
        # Reply to a message with the id = platform_message_id
        pass