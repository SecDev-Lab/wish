#!/usr/bin/env python
"""Run the wish-sh TUI application."""

from wish_sh.tui.app import WishTUIApp

if __name__ == "__main__":
    app = WishTUIApp()
    app.run()
