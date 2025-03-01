"""Tests for the TUI modes."""

import pytest

from wish_sh.tui.modes import WishMode


class TestWishMode:
    """Tests for the WishMode enum."""

    def test_wish_mode_values(self):
        """Test that the WishMode enum has the expected values."""
        # Check that the enum has the expected members
        assert hasattr(WishMode, "NEW_WISH")
        assert hasattr(WishMode, "WISH_HISTORY")
        
        # Check that the members are different
        assert WishMode.NEW_WISH != WishMode.WISH_HISTORY
    
    def test_wish_mode_comparison(self):
        """Test that WishMode values can be compared."""
        # Same mode should be equal
        assert WishMode.NEW_WISH == WishMode.NEW_WISH
        assert WishMode.WISH_HISTORY == WishMode.WISH_HISTORY
        
        # Different modes should not be equal
        assert WishMode.NEW_WISH != WishMode.WISH_HISTORY
        
        # Mode should be comparable to itself
        mode = WishMode.NEW_WISH
        assert mode == WishMode.NEW_WISH
        
        # Mode should be usable in conditionals
        if mode == WishMode.NEW_WISH:
            assert True
        else:
            assert False
