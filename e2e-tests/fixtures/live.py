"""Live environment helpers for E2E testing."""

import ipaddress
import logging
from unittest.mock import AsyncMock

from wish_ai.conversation.manager import ConversationManager
from wish_ai.gateway.openai import OpenAIGateway
from wish_ai.planning.generator import PlanGenerator
from wish_cli.core.command_dispatcher import CommandDispatcher
from wish_cli.headless import HeadlessWish
from wish_core.config.manager import ConfigManager
from wish_core.session import InMemorySessionManager
from wish_core.state.manager import InMemoryStateManager
from wish_tools.execution.executor import ToolExecutor

logger = logging.getLogger(__name__)

# Environment control flags - no longer needed
# USE_LIVE_ENV = True  # Always enabled when using this module

# Safety configurations
ALLOWED_TARGET_RANGES = [
    "10.10.10.0/24",  # HTB EU VPN range
    "10.10.11.0/24",  # HTB EU VPN range
    "10.129.0.0/16",  # HTB US VPN range
]

DANGEROUS_COMMANDS = [
    "rm -rf /",
    "format",
    "shutdown",
    "reboot",
    "> /dev/sda",
    "dd if=/dev/zero",
    "mkfs",
    ":(){:|:&};:",  # Fork bomb
]

ALLOWED_TOOLS = [
    "nmap",
    "nikto",
    "gobuster",
    "enum4linux",
    "smbclient",
    "rpcclient",
    "nbtscan",
    "onesixtyone",
    "snmpwalk",
    "hydra",
    "medusa",
    "wpscan",
    "sqlmap",
    "dirbuster",
    "dirb",
    "wfuzz",
    "ffuf",
    "masscan",
    "unicornscan",
    "amap",
    "sslscan",
    "sslyze",
    "testssl.sh",
]


def is_target_allowed(ip: str) -> bool:
    """Check if target IP is in allowed ranges."""
    try:
        target = ipaddress.ip_address(ip)
        return any(
            target in ipaddress.ip_network(allowed)
            for allowed in ALLOWED_TARGET_RANGES
        )
    except ValueError:
        logger.error(f"Invalid IP address: {ip}")
        return False


def is_command_safe(command: str) -> bool:
    """Check if command is safe to execute."""
    cmd_lower = command.lower()

    # Check for dangerous patterns
    for danger in DANGEROUS_COMMANDS:
        if danger.lower() in cmd_lower:
            logger.warning(f"Dangerous command blocked: {command}")
            return False

    # Check if using allowed tools only
    cmd_parts = command.split()
    if cmd_parts:
        tool = cmd_parts[0].split("/")[-1]  # Handle full paths
        if tool not in ALLOWED_TOOLS:
            # Allow basic shell commands
            if tool not in ["echo", "cd", "pwd", "ls", "cat", "grep", "awk", "sed"]:
                logger.warning(f"Unallowed tool blocked: {tool}")
                return False

    return True


class SafeToolExecutor(ToolExecutor):
    """Tool executor with safety checks."""

    async def execute(self, command: str, timeout: int | None = None) -> dict:
        """Execute command with safety validation."""
        if not is_command_safe(command):
            raise ValueError(f"Unsafe command blocked: {command}")

        # Extract target IPs from command
        import re
        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
        ips = re.findall(ip_pattern, command)

        # Verify all targets are allowed
        for ip in ips:
            if not is_target_allowed(ip):
                raise ValueError(f"Target IP not in allowed range: {ip}")

        # Execute with parent class
        return await super().execute(command, timeout)


class LiveHeadlessWish(HeadlessWish):
    """HeadlessWish configured for live environment testing."""

    def __init__(self, auto_approve: bool = False):
        """Initialize with auto_approve setting."""
        self._auto_approve = auto_approve
        super().__init__(auto_approve=auto_approve)

    async def _send_prompt(self, session_id: str, prompt: str):
        """Override to handle command_dispatcher's bool return value."""
        import copy
        import time

        from wish_cli.headless import PromptResult

        state_before = await self.state_manager.get_current_state()
        state_before = copy.deepcopy(state_before)

        start_time = time.time()

        # Process command (returns bool, not string)
        success = await self.command_dispatcher.process_command(prompt)

        execution_time = time.time() - start_time
        state_after = await self.state_manager.get_current_state()

        # Track command for history
        self.command_dispatcher.command_history.append(prompt)

        return PromptResult(
            prompt=prompt,
            result="Command executed successfully" if success else "Command execution failed",
            state_before=state_before,
            state_after=state_after,
            execution_time=execution_time
        )

    async def _end_session(self, session_id: str):
        """Override to handle command_history."""
        import time

        from wish_cli.headless import SessionSummary

        if not self._active_session:
            raise ValueError("No active session")

        duration = time.time() - self._active_session.created_at
        current_state = await self.state_manager.get_current_state()

        # Save session
        await self.session_manager.save_session(current_state)

        # Clean up resources
        await self._cleanup_resources()

        # Create summary
        summary = SessionSummary(
            session_id=session_id,
            duration=duration,
            prompts_executed=len(self.command_dispatcher.command_history),
            hosts_discovered=len(current_state.hosts) if current_state.hosts else 0,
            findings=len(current_state.findings) if current_state.findings else 0
        )

        self._active_session = None
        return summary

    async def _cleanup_resources(self):
        """Clean up any remaining resources."""
        # Close AI gateway client if it has an async close method
        if hasattr(self.ai_gateway, 'close'):
            try:
                await self.ai_gateway.close()
            except Exception as e:
                logger.warning(f"Error closing AI gateway: {e}")

    def _initialize_components(self):
        """Initialize with real components for live testing."""
        logger.info("Initializing LiveHeadlessWish with real components")

        # Real components
        self.config_manager = ConfigManager()
        self.session_manager = InMemorySessionManager()
        self.state_manager = InMemoryStateManager()

        # AI components with real OpenAI
        self.ai_gateway = OpenAIGateway()

        # Tool executor with safety checks
        self.tool_executor = SafeToolExecutor()

        # UI Manager - use HeadlessUIManager for test mode
        from wish_cli.headless.client import HeadlessUIManager
        self.ui_manager = HeadlessUIManager(auto_approve=self._auto_approve)

        # Override request_plan_approval if needed
        if self._auto_approve:
            # Auto-approve all plans
            async def auto_approve_plans(plan):
                logger.info("Auto-approving plan in test mode")
                return True
            self.ui_manager.request_plan_approval = auto_approve_plans
        else:
            # Reject all plans to prevent execution
            async def reject_all_plans(plan):
                logger.info("Rejecting plan in test mode (auto_approve=False)")
                return False
            self.ui_manager.request_plan_approval = reject_all_plans

        # Conversation Manager
        self.conversation_manager = ConversationManager()

        # Plan Generator
        self.plan_generator = PlanGenerator(self.ai_gateway)

        # Command Dispatcher with all dependencies
        self.command_dispatcher = CommandDispatcher(
            ui_manager=self.ui_manager,
            state_manager=self.state_manager,
            session_manager=self.session_manager,
            conversation_manager=self.conversation_manager,
            plan_generator=self.plan_generator,
            tool_executor=self.tool_executor
        )

        # Add command_history attribute for compatibility
        self.command_dispatcher.command_history = []

        # Event collector for testing
        self.event_collector = AsyncMock()

        logger.info("LiveHeadlessWish initialization complete")


def create_live_headless_wish(auto_approve: bool = False) -> LiveHeadlessWish:
    """Create a live environment HeadlessWish instance."""
    # Verify OpenAI API key is available (from env or config)
    from wish_core.config import get_api_key
    api_key = get_api_key()
    if not api_key:
        raise RuntimeError(
            "OpenAI API key not found. Set OPENAI_API_KEY environment variable "
            "or configure in ~/.wish/config.toml"
        )

    return LiveHeadlessWish(auto_approve=auto_approve)


def verify_htb_connectivity(target_ip: str = "10.10.10.3") -> bool:
    """Verify connectivity to HTB target."""
    import subprocess

    try:
        # Simple ping test
        result = subprocess.run(  # noqa: S603
            ["ping", "-c", "1", "-W", "2", target_ip],  # noqa: S607
            capture_output=True,
            text=True
        )
        return result.returncode == 0
    except Exception as e:
        logger.error(f"Failed to verify connectivity: {e}")
        return False
