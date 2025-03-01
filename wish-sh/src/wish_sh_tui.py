#!/usr/bin/env python3
"""Entry point for the wish-sh TUI."""

from wish_sh.tui.app import WishTUIApp


def main():
    """Run the wish-sh TUI application."""
    app = WishTUIApp()
    app.run()


if __name__ == "__main__":
    main()
