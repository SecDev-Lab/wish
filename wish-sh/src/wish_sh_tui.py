#!/usr/bin/env python3
"""Entry point for the wish-sh TUI."""

import os
from wish_sh.tui.app import WishTUIApp


def main():
    """Run the wish-sh TUI application."""
    os.environ["TEXTUAL_USE_WIDECHARS"] = "1"

    app = WishTUIApp()
    app.run()


if __name__ == "__main__":
    main()
