from enum import Enum


class WishState(str, Enum):
    DOING = "DOING"
    DONE = "DONE"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"
