"""Basic tests for wish-cli functionality."""

from unittest.mock import AsyncMock, Mock

import pytest
from wish_core.session import SessionManager
from wish_core.state.manager import StateManager
from wish_models.session import SessionMetadata

from wish_cli.cli.hybrid import HybridWishCLI as WishCLI
from wish_cli.core.command_dispatcher import CommandDispatcher
from wish_cli.ui.ui_manager import WishUIManager


class TestWishCLI:
    """Test WishCLI main class."""

    @pytest.fixture
    def mock_ui_manager(self):
        """Mock UI manager."""
        ui_manager = Mock(spec=WishUIManager)
        ui_manager.initialize = AsyncMock()
        ui_manager.shutdown = AsyncMock()
        ui_manager.get_user_input = AsyncMock(return_value="exit")
        ui_manager.print_info = Mock()
        ui_manager.print_error = Mock()
        ui_manager.print = Mock()
        ui_manager.update_status = Mock()
        ui_manager.get_running_jobs = Mock(return_value=[])
        return ui_manager

    @pytest.fixture
    def mock_command_dispatcher(self):
        """Mock command dispatcher."""
        dispatcher = Mock(spec=CommandDispatcher)
        dispatcher.initialize = AsyncMock()
        dispatcher.shutdown = AsyncMock()
        dispatcher.process_command = AsyncMock(return_value=True)
        return dispatcher

    @pytest.fixture
    def mock_session_manager(self):
        """Mock session manager."""
        session_manager = Mock(spec=SessionManager)
        session_manager.create_session = Mock(return_value=SessionMetadata(session_id="test-session"))
        session_manager.save_session = AsyncMock()
        session_manager.get_current_directory = Mock(return_value="/test/dir")
        return session_manager

    @pytest.fixture
    def mock_state_manager(self):
        """Mock state manager."""
        state_manager = Mock(spec=StateManager)
        state_manager.initialize = AsyncMock()
        state_manager.get_current_state = AsyncMock()
        from wish_models.engagement import EngagementState
        from wish_models.session import SessionMetadata

        mock_session = SessionMetadata(session_id="test-session")
        mock_engagement = EngagementState(name="test-engagement", session_metadata=mock_session)
        state_manager.get_current_state = AsyncMock(return_value=mock_engagement)
        return state_manager

    @pytest.fixture
    def wish_cli(self, mock_ui_manager, mock_command_dispatcher, mock_session_manager, mock_state_manager):
        """Create WishCLI instance with mocked dependencies."""
        return WishCLI(
            ui_manager=mock_ui_manager,
            command_dispatcher=mock_command_dispatcher,
            session_manager=mock_session_manager,
            state_manager=mock_state_manager,
        )

    @pytest.mark.asyncio
    async def test_initialization(self, wish_cli, mock_ui_manager, mock_command_dispatcher, mock_state_manager):
        """Test CLI initialization."""
        await wish_cli.initialize()

        # Verify initialization calls
        mock_state_manager.initialize.assert_called_once()
        mock_command_dispatcher.initialize.assert_called_once()

        # Verify session creation
        assert wish_cli.current_session is not None
        assert wish_cli.current_session.session_id == "test-session"

    @pytest.mark.asyncio
    async def test_shutdown(self, wish_cli, mock_command_dispatcher, mock_session_manager, mock_state_manager):
        """Test CLI shutdown."""
        wish_cli.current_session = SessionMetadata(session_id="test-session")

        await wish_cli.shutdown()

        # Verify shutdown calls
        mock_command_dispatcher.shutdown.assert_called_once()
        mock_state_manager.get_current_state.assert_called_once()
        mock_session_manager.save_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_run_with_exit_command(self, wish_cli, mock_ui_manager, mock_state_manager):
        """Test CLI run loop with exit command."""
        # Mock MinimalInputApp
        from unittest.mock import patch

        with patch("wish_cli.ui.minimal_input_app.MinimalInputApp") as MockInputApp:
            mock_app = AsyncMock()
            mock_app.run_async = AsyncMock()
            MockInputApp.return_value = mock_app

            # Run CLI
            await wish_cli.run()

            # Verify initialization
            mock_state_manager.initialize.assert_called_once()
            MockInputApp.assert_called_once()
            mock_app.run_async.assert_called_once_with(inline=True)


class TestCommandDispatcher:
    """Test CommandDispatcher functionality."""

    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies for CommandDispatcher."""
        return {
            "ui_manager": Mock(spec=WishUIManager),
            "state_manager": Mock(spec=StateManager),
            "session_manager": Mock(spec=SessionManager),
            "conversation_manager": Mock(),
            "plan_generator": Mock(),
            "tool_executor": Mock(),
        }

    @pytest.fixture
    def command_dispatcher(self, mock_dependencies):
        """Create CommandDispatcher with mocked dependencies."""
        from wish_cli.commands.slash_commands import SlashCommandHandler

        dispatcher = CommandDispatcher(**mock_dependencies)
        dispatcher.slash_handler = Mock(spec=SlashCommandHandler)
        dispatcher.slash_handler.initialize = AsyncMock()
        dispatcher.slash_handler.shutdown = AsyncMock()
        dispatcher.slash_handler.handle_command = AsyncMock(return_value=True)

        return dispatcher

    @pytest.mark.asyncio
    async def test_slash_command_processing(self, command_dispatcher):
        """Test slash command processing."""
        session = SessionMetadata(session_id="test-session")
        await command_dispatcher.initialize(session)

        # Test slash command
        result = await command_dispatcher.process_command("/help")

        # Verify slash handler was called
        command_dispatcher.slash_handler.handle_command.assert_called_once_with("/help")
        assert result is True

    @pytest.mark.asyncio
    async def test_empty_command_handling(self, command_dispatcher):
        """Test handling of empty commands."""
        session = SessionMetadata(session_id="test-session")
        await command_dispatcher.initialize(session)

        # Test empty command
        result = await command_dispatcher.process_command("")

        # Should return True without processing
        assert result is True
        command_dispatcher.slash_handler.handle_command.assert_not_called()


class TestSlashCommands:
    """Test slash command functionality."""

    @pytest.fixture
    def mock_ui_manager(self):
        """Mock UI manager for slash commands."""
        ui_manager = Mock(spec=WishUIManager)
        ui_manager.print = Mock()
        ui_manager.print_error = Mock()
        ui_manager.get_running_jobs = Mock(return_value=[])
        ui_manager.cancel_job = AsyncMock(return_value=True)
        ui_manager.console = Mock()
        ui_manager.console.clear = Mock()
        return ui_manager

    @pytest.fixture
    def slash_handler(self, mock_ui_manager):
        """Create SlashCommandHandler with mocked dependencies."""
        from wish_cli.commands.slash_commands import SlashCommandHandler

        return SlashCommandHandler(
            ui_manager=mock_ui_manager,
            state_manager=Mock(spec=StateManager),
            session_manager=Mock(spec=SessionManager),
            tool_executor=Mock(),
        )

    @pytest.mark.asyncio
    async def test_help_command(self, slash_handler, mock_ui_manager):
        """Test help command."""
        result = await slash_handler.handle_command("/help")

        assert result is True
        mock_ui_manager.print.assert_called()

    @pytest.mark.asyncio
    async def test_clear_command(self, slash_handler, mock_ui_manager):
        """Test clear command."""
        result = await slash_handler.handle_command("/clear")

        assert result is True
        mock_ui_manager.console.clear.assert_called_once()

    @pytest.mark.asyncio
    async def test_unknown_command(self, slash_handler, mock_ui_manager):
        """Test unknown command handling."""
        result = await slash_handler.handle_command("/unknown")

        assert result is True
        mock_ui_manager.print_error.assert_called_once()

    @pytest.mark.asyncio
    async def test_mode_command(self, slash_handler):
        """Test mode command."""
        # Mock session
        session = SessionMetadata(session_id="test-session", current_mode="recon")
        slash_handler.current_session = session
        slash_handler.session_manager.save_session = AsyncMock()

        result = await slash_handler.handle_command("/mode")

        assert result is True

        # Test mode change
        result = await slash_handler.handle_command("/mode enum")

        assert result is True
        assert session.current_mode == "enum"
