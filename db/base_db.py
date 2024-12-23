from abc import ABC, abstractmethod
from typing import List, Optional
from misc import TSBMessage, Status


class BaseDB(ABC):
    @abstractmethod
    def get_latest_message_id(self) -> Optional[str]:
        # Gets the latest message id from the db so when we want to receive the latest
        # messages from the platform, only look for the ones newest than this one.
        pass

    @abstractmethod
    def insert_messages(self, messages: List[TSBMessage]) -> None:
        # inserts platform messages in the db
        pass

    @abstractmethod
    def get_messages_to_process(self, top: Optional[int]) -> Optional[TSBMessage]:
        # gets latest messages that can be processed,
        # meaning the oldest message with status empty.
        pass

    @abstractmethod
    def get_timestamps(self, message: TSBMessage) -> Optional[str]:
        # gets the timestamps (actual video process output) text
        pass

    @abstractmethod
    def update(self, message: TSBMessage, status: Status) -> None:
        # updates the message with a Status
        pass