from wish_sh.wish_cli import WishCLI


def main():
    """Entry point for the wish shell."""
    # Set environment variable for proper handling of wide characters (emojis)
    cli = WishCLI()
    cli.run()


if __name__ == "__main__":
    main()
