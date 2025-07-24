"""Main entry point for wish-cli."""

import asyncio
import logging
import os
import signal
import sys
from pathlib import Path
from types import FrameType
from typing import Any

from wish_ai.conversation.manager import ConversationManager
from wish_ai.gateway.openai import OpenAIGateway
from wish_ai.planning.generator import PlanGenerator
from wish_c2 import create_c2_connector
from wish_core.config.manager import ConfigManager
from wish_core.persistence import SessionStore
from wish_core.persistence.auto_save import AutoSaveManager
from wish_core.session import FileSessionManager
from wish_core.state.manager import InMemoryStateManager
from wish_knowledge import KnowledgeConfig, Retriever
from wish_knowledge.config import EmbeddingConfig
from wish_knowledge.manager import KnowledgeManager, check_knowledge_initialized
from wish_tools.execution.executor import ToolExecutor

from wish_cli.cli.hybrid import HybridWishCLI as WishCLI
from wish_cli.core.command_dispatcher import CommandDispatcher
from wish_cli.ui.ui_manager import WishUIManager

logger = logging.getLogger(__name__)


class WishApp:
    """Main application class for wish-cli."""

    def __init__(self) -> None:
        self.cli: WishCLI | None = None
        self.ui_manager: WishUIManager | None = None
        self.shutdown_event = asyncio.Event()
        self.auto_save_manager: AutoSaveManager | None = None

    async def initialize(self) -> None:
        """Initialize all components."""
        # Configuration
        config_manager = ConfigManager()
        config = config_manager.load_config()

        # Setup logging based on debug mode
        import logging
        import logging.handlers
        from pathlib import Path

        # Create logs directory
        log_dir = Path.home() / ".wish" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "wish.log"

        # Setup logging format
        log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"

        # Create handlers
        handlers = []

        # File handler with rotation
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding="utf-8",
        )
        file_handler.setFormatter(logging.Formatter(log_format))
        handlers.append(file_handler)

        # Configure logging
        log_level = logging.DEBUG if config.general.debug_mode else logging.INFO
        logging.basicConfig(level=log_level, format=log_format, handlers=handlers, force=True)

        if config.general.debug_mode:
            logging.getLogger("wish_ai").setLevel(logging.DEBUG)
            logging.getLogger("wish_cli").setLevel(logging.DEBUG)
            logging.getLogger("wish_core").setLevel(logging.DEBUG)
            # Output to log file only (not to console)
            print(f"Debug mode enabled - logs written to {log_file}")
            logging.info(f"Debug mode enabled - logs written to {log_file}")
            logging.debug(f"LLM config: model={config.llm.model}, timeout={config.llm.timeout}s")
        else:
            # Suppress verbose logs from libraries
            logging.getLogger("httpx").setLevel(logging.WARNING)
            logging.getLogger("openai").setLevel(logging.WARNING)
            # Output to log file only (not to console)
            print(f"Logs written to {log_file}")
            logging.info(f"Logs written to {log_file}")

        # Core components
        session_store = SessionStore()
        session_manager = FileSessionManager(session_store)
        state_manager = InMemoryStateManager()

        # AI components
        ai_gateway = OpenAIGateway(
            api_key=config.llm.api_key,
            model=config.llm.model,
            max_tokens=config.llm.max_tokens,
            temperature=config.llm.temperature,
            timeout=config.llm.timeout,
        )
        conversation_manager = ConversationManager()
        plan_generator = PlanGenerator(ai_gateway)

        # Tool execution
        tool_executor = ToolExecutor()

        # Initialize knowledge base
        knowledge_config = KnowledgeConfig(
            auto_import=config.knowledge.auto_import if hasattr(config, "knowledge") else True,
            embedding=EmbeddingConfig(
                api_key=config.llm.api_key,  # Reuse LLM API key
                model="text-embedding-3-large",
            ),
        )

        # Create retriever for AI context
        retriever = None
        if check_knowledge_initialized():
            logger.info("Knowledge base already initialized, creating retriever")
            retriever = Retriever(config=knowledge_config)
        else:
            # Initialize knowledge base in foreground (blocking)
            logger.info("First time setup: Initializing HackTricks knowledge base...")
            knowledge_manager = KnowledgeManager(knowledge_config)

            # Initialize UI early for progress display
            self.ui_manager = WishUIManager()
            await self.ui_manager.initialize()

            # Show initialization message
            self.ui_manager.print_info("[bold cyan]Welcome to wish![/bold cyan]")
            self.ui_manager.print_info("First time setup detected. Importing HackTricks knowledge base...")
            self.ui_manager.print_info("This may take a few minutes. Please wait...")

            # Define progress callback that updates UI
            def knowledge_progress(stage: str, progress: float) -> None:
                if self.ui_manager:
                    self.ui_manager.show_knowledge_progress(stage, progress)

            # Run initialization in foreground and wait for completion
            await knowledge_manager.initialize_foreground(progress_callback=knowledge_progress)

            # Create retriever after initialization
            retriever = Retriever(config=knowledge_config)
            self.ui_manager.print_success("✓ Knowledge base initialized successfully!")

        # C2 connector (optional)
        c2_connector = None
        try:
            # Load Sliver configuration from multiple sources
            sliver_config = self._load_sliver_config()

            if sliver_config.get("enabled", False):
                mode = sliver_config.get("mode", "real")
                connector_config = {
                    "config_path": sliver_config.get("config_path"),
                    "demo_mode": sliver_config.get("demo_mode", False),
                    "safety": sliver_config.get("safety", {}),
                }

                logging.info(f"Creating Sliver C2 connector in {mode} mode")
                c2_connector = create_c2_connector("sliver", mode=mode, config=connector_config)

                # Connect to C2 server
                if await c2_connector.connect():
                    logging.info("Successfully connected to C2 server")
                else:
                    logging.warning("Failed to connect to C2 server")
                    c2_connector = None
        except Exception as e:
            logging.warning(f"Failed to initialize C2 connector: {e}")
            c2_connector = None

        # Auto-save manager
        self.auto_save_manager = AutoSaveManager(
            session_store=session_store,
            save_interval=30,  # Auto-save every 30 seconds
            state_provider=lambda: state_manager.get_current_state_sync(),
        )

        # UI components (initialize only if not already done during knowledge import)
        if not self.ui_manager:
            self.ui_manager = WishUIManager()
            await self.ui_manager.initialize()

        # Command dispatcher
        command_dispatcher = CommandDispatcher(
            ui_manager=self.ui_manager,
            state_manager=state_manager,
            session_manager=session_manager,
            conversation_manager=conversation_manager,
            plan_generator=plan_generator,
            tool_executor=tool_executor,
            c2_connector=c2_connector,
            retriever=retriever,
        )

        # Set command dispatcher reference in UI manager
        self.ui_manager.set_command_dispatcher(command_dispatcher)

        # Main CLI
        self.cli = WishCLI(
            ui_manager=self.ui_manager,
            command_dispatcher=command_dispatcher,
            session_manager=session_manager,
            state_manager=state_manager,
        )

        # Signal handlers
        self._setup_signal_handlers()

        # Start auto-save
        await self.auto_save_manager.start_auto_save()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful shutdown."""

        def signal_handler(signum: int, frame: FrameType | None) -> None:
            print("\nReceived interrupt signal. Shutting down gracefully...")
            self.shutdown_event.set()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    async def run(self) -> None:
        """Run the main application."""
        if not self.cli:
            await self.initialize()

        try:
            # Start CLI
            if self.cli is not None:
                await self.cli.run()
            else:
                raise RuntimeError("CLI not initialized")
        except KeyboardInterrupt:
            print("\nShutdown requested by user.")
        except Exception as e:
            print(f"Critical error: {e}")
            sys.exit(1)
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """Shutdown all components gracefully."""
        # Stop auto-save
        if self.auto_save_manager:
            await self.auto_save_manager.stop_auto_save()

        if self.cli:
            await self.cli.shutdown()

        if self.ui_manager:
            await self.ui_manager.shutdown()

    def _load_sliver_config(self) -> dict[str, Any]:
        """Load Sliver configuration from multiple sources.

        Priority order:
        1. Environment variables
        2. Config file settings
        3. Auto-detected default config paths

        Returns:
            Dictionary with Sliver configuration
        """
        config: dict[str, Any] = {
            "enabled": False,
            "mode": "real",
            "config_path": None,
            "demo_mode": False,
            "safety": {
                "sandbox_mode": False,
                "read_only": False,
            },
        }

        # 1. Check environment variables first
        if os.getenv("WISH_C2_ENABLED", "").lower() in ["true", "1", "yes", "on"]:
            config["enabled"] = True

        if mode := os.getenv("WISH_C2_MODE"):
            config["mode"] = mode

        if config_path := os.getenv("WISH_C2_SLIVER_CONFIG"):
            config["config_path"] = config_path
            config["enabled"] = True  # Auto-enable if config provided

        # 2. Auto-detect Sliver config files if not provided
        if not config["config_path"]:
            default_paths = [
                "~/.sliver-client/configs/wish.cfg",  # Primary
                "~/.sliver-client/configs/wish-test.cfg",  # Development
                "~/.sliver-client/configs/default.cfg",  # Fallback
            ]

            for path_str in default_paths:
                path = Path(path_str).expanduser()
                if path.exists():
                    config["config_path"] = str(path)
                    config["enabled"] = True
                    logger.info(f"Auto-detected Sliver config: {path}")
                    break

        # 3. Safety settings from environment
        if os.getenv("WISH_C2_SANDBOX", "").lower() in ["true", "1", "yes", "on"]:
            config["safety"]["sandbox_mode"] = True

        if os.getenv("WISH_C2_READONLY", "").lower() in ["true", "1", "yes", "on"]:
            config["safety"]["read_only"] = True

        # Log configuration summary
        if config["enabled"]:
            logger.info(f"Sliver C2 enabled: mode={config['mode']}, config_path={config['config_path']}")
        else:
            logger.info("Sliver C2 disabled - no config found or not enabled")

        return config


async def async_main() -> None:
    """Async main entry point."""
    app = WishApp()
    await app.run()


def main() -> None:
    """Main entry point for the wish CLI."""
    try:
        asyncio.run(async_main())
    except KeyboardInterrupt:
        print("\nGoodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
