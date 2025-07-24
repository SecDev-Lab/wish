"""Scope management service for wish CLI."""

import logging
from typing import TYPE_CHECKING

from wish_models.engagement import Target

if TYPE_CHECKING:
    from wish_core.state.manager import StateManager

logger = logging.getLogger(__name__)


class ScopeManager:
    """Manages target scope operations."""

    def __init__(self, state_manager: "StateManager"):
        self.state_manager = state_manager

    async def show_current_scope(self) -> list[str]:
        """Get current scope information as formatted strings."""
        engagement_state = await self.state_manager.get_current_state()

        if not engagement_state.targets:
            return ["[wish.step]●[/wish.step] [dim]No scope defined[/dim]"]

        lines = ["[wish.step]●[/wish.step] Target Scope:"]
        for target in engagement_state.targets.values():
            lines.append(f"  [wish.step]⎿[/wish.step] [cyan]{target.scope}[/cyan] ({target.scope_type})")
        return lines

    async def add_target(self, target_scope: str) -> tuple[bool, str]:
        """Add a target to scope."""
        try:
            # Determine scope type
            if "/" in target_scope:
                scope_type = "cidr"
            elif target_scope.replace(".", "").replace(":", "").isdigit():
                scope_type = "ip"
            elif target_scope.startswith("http://") or target_scope.startswith("https://"):
                scope_type = "url"
            else:
                scope_type = "domain"

            target = Target(
                scope=target_scope,
                scope_type=scope_type,  # type: ignore[arg-type]
                name=None,
                description=None,
                in_scope=True,
                engagement_rules=None,
            )
            await self.state_manager.add_target(target)

            return True, f"[wish.step]●[/wish.step] Added [cyan]{target_scope}[/cyan] to scope"
        except Exception as e:
            logger.error(f"Failed to add target: {e}")
            return False, f"[error]Could not add target: {e}[/error]"

    async def remove_target(self, target_scope: str) -> tuple[bool, str]:
        """Remove a target from scope."""
        try:
            await self.state_manager.remove_target(target_scope)
            return True, f"[wish.step]●[/wish.step] Removed [cyan]{target_scope}[/cyan] from scope"
        except Exception as e:
            logger.error(f"Failed to remove target: {e}")
            return False, f"[error]Could not remove target: {e}[/error]"

    async def process_scope_command(self, command: str) -> list[str]:
        """Process scope command and return output lines."""
        parts = command.split()
        args = parts[1:] if len(parts) > 1 else []

        if not args:
            return await self.show_current_scope()

        operation = args[0].lower()
        if operation == "add" and len(args) > 1:
            success, message = await self.add_target(args[1])
            return [message]
        elif operation == "remove" and len(args) > 1:
            success, message = await self.remove_target(args[1])
            return [message]
        else:
            return ["[error]Usage: /scope [add|remove] <target>[/error]"]
