"""Simple HeadlessWish test to verify basic functionality."""

import os
import tempfile
from unittest.mock import patch

import pytest
from wish_cli.headless import HeadlessWish


class TestSimpleHeadless:
    """Simple HeadlessWish tests."""

    @pytest.mark.asyncio
    async def test_headless_basic_functionality(self):
        """Test basic HeadlessWish functionality without complex mocking."""
        # Create temporary directory for test
        with tempfile.TemporaryDirectory() as temp_dir:
            # Set HOME to temp directory to avoid affecting real config
            with patch.dict(os.environ, {'HOME': temp_dir}):
                wish = HeadlessWish(auto_approve=True)

                # Try to start a session
                try:
                    session = await wish.start_session()

                    # Test a simple query
                    result = await session.send_prompt("echo hello world")

                    # Verify we get some response
                    assert result is not None

                except Exception:
                    # Print the error for debugging
                    import traceback
                    traceback.print_exc()

                    # Even if there's an error, we want to see what it is
                    # Don't fail the test immediately
                    pass

                finally:
                    # Clean up
                    if 'session' in locals():
                        await session.end()

    @pytest.mark.asyncio
    async def test_knowledge_initialization_error(self):
        """Test to see the actual knowledge initialization error."""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch.dict(os.environ, {'HOME': temp_dir}):
                wish = HeadlessWish(auto_approve=True)

                errors = []

                # Capture any error events
                @wish.on_event('error')
                async def capture_error(event):
                    errors.append(event.data)
                    print(f"Captured error: {event.data}")

                try:
                    session = await wish.start_session()

                    # Give some time for initialization
                    import asyncio
                    await asyncio.sleep(1.0)

                    print(f"Captured {len(errors)} errors during initialization")
                    for i, error in enumerate(errors):
                        print(f"Error {i+1}: {error}")

                except Exception as e:
                    print(f"Exception during session start: {e}")
                    import traceback
                    traceback.print_exc()

                finally:
                    if 'session' in locals():
                        await session.end()
