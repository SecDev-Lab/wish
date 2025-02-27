import os

# Constants
DEFAULT_WISH_HOME = os.path.join(os.path.expanduser("~"), ".wish")


class Settings:
    def __init__(self):
        self.WISH_HOME = os.environ.get("WISH_HOME", DEFAULT_WISH_HOME)
