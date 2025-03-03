from wish_sh.tui.app import WishTUIApp


def main():
    """Entry point for the wish shell."""
    # Set environment variable for proper handling of wide characters (emojis)
    app = WishTUIApp()
    app.run()


if __name__ == "__main__":
    main()
