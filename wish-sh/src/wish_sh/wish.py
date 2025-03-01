import os
from wish_sh.wish_cli import WishCLI


def main():
    """Entry point for the wish shell."""
    # Set environment variable for proper handling of wide characters (emojis)
    os.environ["TEXTUAL_USE_WIDECHARS"] = "1"
    
    cli = WishCLI()
    cli.run()


if __name__ == "__main__":
    main()
