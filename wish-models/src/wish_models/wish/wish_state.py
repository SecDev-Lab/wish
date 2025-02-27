from enum import Enum


class WishState(Enum):
    DOING = "DOING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
