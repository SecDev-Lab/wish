from unittest.mock import patch

from wish_sh.wish_cli import WishCLI


# Test for main function
@patch.object(WishCLI, "run")
def test_main(mock_run):
    """Test that main function creates a WishCLI instance and runs it."""
    from wish_sh.wish import main

    main()

    mock_run.assert_called_once()
