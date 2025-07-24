"""Scope command handler for wish CLI."""

import logging
from typing import Any

from wish_core.state.manager import StateManager
from wish_models.engagement import Target

logger = logging.getLogger(__name__)


class ScopeCommandHandler:
    """Scope command handler for managing target scope."""

    def __init__(self, state_manager: StateManager, input_app: Any | None = None):
        self.state_manager = state_manager
        self.input_app = input_app

    def set_input_app(self, input_app: Any) -> None:
        """Set the input app for output operations."""
        self.input_app = input_app

    async def handle_scope(self, command: str) -> None:
        """Handle scope command."""
        if not self.input_app:
            return

        # Parse command line
        parts = command.split()
        args = parts[1:] if len(parts) > 1 else []

        try:
            if not args:
                # Display current scope
                engagement_state = await self.state_manager.get_current_state()
                if engagement_state.targets:
                    self.input_app.write_output("[wish.step]●[/wish.step] Target Scope:")
                    for target in engagement_state.targets.values():
                        self.input_app.write_output(
                            f"  [wish.step]⎿[/wish.step] [cyan]{target.scope}[/cyan] ({target.scope_type})"
                        )
                else:
                    self.input_app.write_output("[wish.step]●[/wish.step] [dim]No scope defined[/dim]")
                return

            # Scope operations
            operation = args[0].lower()
            if operation == "add" and len(args) > 1:
                await self._add_target(args[1])
            elif operation == "remove" and len(args) > 1:
                await self._remove_target(args[1])
            else:
                self.input_app.write_output("[error]Usage: /scope [add|remove] <target>[/error]")

        except Exception as e:
            logger.error(f"Scope command error: {e}")
            self.input_app.write_output(f"[error]Scope command error: {e}[/error]")

    async def _add_target(self, target_scope: str) -> None:
        """Add a target to the scope."""
        try:
            # Create new target - determine appropriate scope type
            if "/" in target_scope:
                # CIDR notation
                scope_type = "cidr"
            elif target_scope.replace(".", "").replace(":", "").isdigit():
                # IP address (IPv4/IPv6)
                scope_type = "ip"
            elif target_scope.startswith("http://") or target_scope.startswith("https://"):
                # URL
                scope_type = "url"
            else:
                # Domain name
                scope_type = "domain"

            target = Target(
                scope=target_scope,
                scope_type=scope_type,  # type: ignore[arg-type]
                name=None,
                description=None,
                in_scope=True,
                engagement_rules=None,
            )

            # Add to state manager
            await self.state_manager.add_target(target)
            if self.input_app:
                self.input_app.write_output(f"[wish.step]●[/wish.step] Added [cyan]{target_scope}[/cyan] to scope")
        except Exception as e:
            logger.error(f"Failed to add target: {e}")
            if self.input_app:
                self.input_app.write_output(f"[error]Could not add target: {e}[/error]")

    async def _remove_target(self, target_scope: str) -> None:
        """Remove a target from the scope."""
        try:
            # Remove from state manager
            await self.state_manager.remove_target(target_scope)
            if self.input_app:
                self.input_app.write_output(f"[wish.step]●[/wish.step] Removed [cyan]{target_scope}[/cyan] from scope")
        except Exception as e:
            logger.error(f"Failed to remove target: {e}")
            if self.input_app:
                self.input_app.write_output(f"[error]Could not remove target: {e}[/error]")
