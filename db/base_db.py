from abc import ABC, abstractmethod
from typing import List, Optional, Dict
from misc import TSBMessage, Status


class BaseDB(ABC):
    @abstractmethod
    async def get_latest_message_id(self) -> Optional[str]:
        # Gets the latest message id from the db so when we want to receive the latest
        # messages from the platform, only look for the ones newest than this one.
        pass

    @abstractmethod
    async def insert_jobrun(self, messages: List[TSBMessage]) -> None:
        # inserts infos about the job run into the db
        pass

    @abstractmethod
    async def insert_message(self, messages: TSBMessage) -> None:
        # inserts a platform message in the db
        pass

    @abstractmethod
    async def get_messages_to_process(self, limit: Optional[int]) -> Optional[TSBMessage]:
        # gets latest messages that can be processed,
        # meaning the oldest message with status empty.
        pass

    @abstractmethod
    async def get_timestamps(self, video_id: str) -> Optional[str]:
        # gets the timestamps (actual video process output) text
        pass

    @abstractmethod
    async def update(self, message: TSBMessage, status: Status) -> None:
        # updates the message with a Status
        pass