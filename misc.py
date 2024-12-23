from dataclasses import dataclass
from datetime import datetime
from enum import Enum

@dataclass
class TSBMessage:
    id: int
    status: int
    msg_text: str
    msg_from: str
    msg_id: str

class Status(Enum):
    empty = 0
    process_start = 1
    process_end = 2
    answered = 3,
    invalid = 4