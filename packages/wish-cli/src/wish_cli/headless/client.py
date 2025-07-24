"""Headless client implementation for wish-cli."""

import asyncio
import logging
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any
from unittest.mock import AsyncMock

from rich.text import Text
from wish_ai.planning.models import Plan
from wish_models.engagement import EngagementState
from wish_models.session import SessionMetadata

from wish_cli.ui.ui_manager import WishUIManager

from .models import PromptResult, SessionSummary

logger = logging.getLogger(__name__)


class HeadlessUIManager(WishUIManager):
    """Minimal UI manager for headless mode."""

    def __init__(self, auto_approve: bool = True):
        super().__init__()
        self.logs: list[tuple[str, str]] = []
        self.background_jobs: dict[str, Any] = {}
        self.auto_approve = auto_approve
        # Track log position for each command
        self._command_log_start = 0
        # Track active jobs for /jobs command
        self._active_jobs: dict[str, Any] = {}

    def set_command_dispatcher(self, dispatcher: Any) -> None:
        """Set command dispatcher reference."""
        self._command_dispatcher = dispatcher

    def print(self, message: str) -> None:
        """Print message with Rich markup stripped."""
        # Handle Rich objects (Table, Panel, etc.)
        if not isinstance(message, str):
            # For Rich objects, convert to string first
            from io import StringIO

            from rich.console import Console

            string_io = StringIO()
            console = Console(file=string_io, force_terminal=False, width=120)
            console.print(message)
            message = string_io.getvalue()

        # Remove Rich markup and convert to plain text
        text_obj = Text.from_markup(message)
        plain_text = text_obj.plain
        self.logs.append(("info", plain_text))

    def print_info(self, message: str) -> None:
        """Print info message with Rich markup stripped."""
        text_obj = Text.from_markup(message)
        plain_text = text_obj.plain
        self.logs.append(("info", plain_text))

    def print_warning(self, message: str) -> None:
        """Print warning message with Rich markup stripped."""
        text_obj = Text.from_markup(message)
        plain_text = text_obj.plain
        self.logs.append(("warning", plain_text))

    def print_error(self, message: str) -> None:
        """Print error message with Rich markup stripped."""
        text_obj = Text.from_markup(message)
        plain_text = text_obj.plain
        self.logs.append(("error", plain_text))

    def print_success(self, message: str) -> None:
        """Print success message with Rich markup stripped."""
        text_obj = Text.from_markup(message)
        plain_text = text_obj.plain
        self.logs.append(("success", plain_text))

    def show_progress(self, message: str) -> None:
        """Show progress message."""
        text_obj = Text.from_markup(message)
        plain_text = text_obj.plain
        self.logs.append(("progress", plain_text))

    def display_plan(self, plan: Plan) -> None:
        """Display execution plan."""
        self.logs.append(("plan", f"Plan: {plan.description}"))
        for step in plan.steps:
            self.logs.append(("plan_step", f"  - {step.tool_name}: {step.command}"))

    def print_plan(self, plan: Plan) -> None:
        """Print execution plan (alias for display_plan)."""
        self.display_plan(plan)

    async def request_plan_approval(self, plan: Plan) -> bool:
        """Request plan approval (auto-approve in headless)."""
        if self.auto_approve:
            self.logs.append(("plan_approval", "Plan auto-approved in headless mode"))
            return True
        else:
            self.logs.append(("plan_approval", "Plan rejected in headless mode"))
            return False

    def display_job_started(self, job_id: str, description: str) -> None:
        """Display job started message."""
        self.logs.append(("job_started", f"Started job {job_id}: {description}"))

    def display_job_completed(self, job_id: str) -> None:
        """Display job completed message."""
        self.logs.append(("job_completed", f"Completed job {job_id}"))

    def display_background_jobs(self) -> None:
        """Display background jobs status."""
        if self.background_jobs:
            self.logs.append(("jobs", f"Active jobs: {len(self.background_jobs)}"))
        else:
            self.logs.append(("jobs", "No active jobs"))

    def display_state_update(self, message: str) -> None:
        """Display state update message."""
        self.logs.append(("state_update", message))

    def start_job_display(self, job_ids: list[str]) -> None:
        """Display started jobs."""
        if len(job_ids) == 1:
            self.logs.append(("info", f"Started 1 job: {job_ids[0]}"))
        else:
            self.logs.append(("info", f"Started {len(job_ids)} jobs in parallel: {', '.join(job_ids)}"))
        self.logs.append(("info", "Use '/jobs' to monitor progress, '/status' for current state"))

    def add_background_job(self, job_id: str, job_info: dict) -> None:
        """Add background job."""
        self.background_jobs[job_id] = job_info

    def get_background_job(self, job_id: str) -> dict | None:
        """Get background job info."""
        return self.background_jobs.get(job_id)

    def show_info(self, message: str) -> None:
        """Display info message with [ℹ] icon."""
        text_obj = Text.from_markup(f"[ℹ] {message}")
        plain_text = text_obj.plain
        self.logs.append(("info", plain_text))

    def show_error(self, message: str) -> None:
        """Display error message with [✗] icon."""
        text_obj = Text.from_markup(f"[✗] {message}")
        plain_text = text_obj.plain
        self.logs.append(("error", plain_text))

    def show_success(self, message: str) -> None:
        """Display success message with [✔] icon."""
        text_obj = Text.from_markup(f"[✔] {message}")
        plain_text = text_obj.plain
        self.logs.append(("success", plain_text))

    def print_step_execution(self, tool_name: str, job_id: str) -> None:
        """Print step execution start message."""
        text_obj = Text.from_markup(f"Executing {tool_name} (job: {job_id})")
        plain_text = text_obj.plain
        self.logs.append(("info", plain_text))

    def print_step_completion(self, tool_name: str, job_id: str, success: bool) -> None:
        """Print step completion message."""
        status = "completed" if success else "failed"
        text_obj = Text.from_markup(f"Step {tool_name} (job: {job_id}) {status}")
        plain_text = text_obj.plain
        self.logs.append(("info", plain_text))

    async def start_background_job(
        self,
        job_id: str,
        description: str,
        job_coroutine: Any,
        command: str | None = None,
        tool_name: str | None = None,
        step_info: dict[str, Any] | None = None,
    ) -> None:
        """Start background job with actual execution."""
        self.logs.append(("info", f"Starting job {job_id}: {description}"))

        # Parameters are now provided directly instead of through kwargs

        # Define completion callback for job manager
        def completion_callback(completed_job_id: str, job_info: Any) -> None:
            """Called when job completes."""
            if job_info.status.value == "completed":
                self.logs.append(("info", f"Job {completed_job_id} completed successfully"))
                # Handle state update via command dispatcher
                if self._command_dispatcher and hasattr(self._command_dispatcher, "handle_job_completion"):
                    asyncio.create_task(self._command_dispatcher.handle_job_completion(completed_job_id, job_info))
            elif job_info.status.value == "failed":
                self.logs.append(("error", f"Job {completed_job_id} failed: {job_info.error}"))

        # Use JobManager to start the job
        try:
            actual_job_id = await self.job_manager.start_job(
                job_coroutine=job_coroutine,
                description=description,
                job_id=job_id,
                completion_callback=completion_callback,
                command=command,
                tool_name=tool_name,
                step_info=step_info,
            )

            # Track the job
            self._active_jobs[actual_job_id] = {
                "description": description,
                "tool_name": tool_name,
                "status": "running",
                "started_at": time.time(),
            }

        except Exception as e:
            logger.error(f"Failed to start job {job_id}: {e}")
            self.logs.append(("error", f"Failed to start job {job_id}: {str(e)}"))

    def update_job_status(self, job_id: str, status: str, result: Any = None) -> None:
        """Update job status."""
        if job_id in self.background_jobs:
            self.background_jobs[job_id]["status"] = status
            if result is not None:
                self.background_jobs[job_id]["result"] = result

    def remove_background_job(self, job_id: str) -> None:
        """Remove completed job."""
        if job_id in self.background_jobs:
            del self.background_jobs[job_id]

    async def show_jobs_status(self) -> None:
        """Show jobs status (handled by command dispatcher)."""
        if self._command_dispatcher:
            # Use command dispatcher's slash command handling
            from wish_cli.core.job_manager import JobStatus

            job_infos = []
            for job_id, job_info in self.job_manager.jobs.items():
                if job_info.status == JobStatus.RUNNING:
                    job_infos.append((job_id, job_info))

            if job_infos:
                self.logs.append(("info", "Active jobs:"))
                for job_id, job_info in job_infos:
                    self.logs.append(("info", f"[{job_id}] {job_info.description} - {job_info.status.value}"))


@dataclass
class HeadlessSession:
    """Represents a headless CLI session."""

    session_id: str
    wish_client: "HeadlessWish"
    metadata: dict[str, Any]
    created_at: float

    async def send_prompt(self, prompt: str) -> PromptResult:
        """Send a prompt to the session."""
        return await self.wish_client._send_prompt(self.session_id, prompt)

    async def get_state(self) -> EngagementState:
        """Get current engagement state."""
        return await self.wish_client._get_state()

    async def end(self) -> SessionSummary:
        """End the session."""
        return await self.wish_client._end_session(self.session_id)


class HeadlessWish:
    """Headless mode Python SDK for wish."""

    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve
        self._event_handlers: dict[str, list[Callable]] = {}
        self._active_session: HeadlessSession | None = None
        self._last_log_index = 0  # Track log position for headless output

        # Initialize components
        self._initialize_components()

    def _initialize_components(self) -> None:
        """Initialize core components."""
        logger.info("HeadlessWish initializing with real components")

        # Import real components
        from wish_ai.conversation.manager import ConversationManager
        from wish_ai.gateway.openai import OpenAIGateway
        from wish_ai.planning.generator import PlanGenerator
        from wish_core.config import ConfigManager
        from wish_core.session import InMemorySessionManager
        from wish_core.state.manager import InMemoryStateManager
        from wish_tools.execution.executor import ToolExecutor

        from wish_cli.core.command_dispatcher import CommandDispatcher

        # Initialize real config manager
        self.config_manager = ConfigManager()

        # Initialize real session manager
        self.session_manager = InMemorySessionManager()

        # Initialize real state manager
        self.state_manager = InMemoryStateManager()

        # Initialize conversation manager
        self.conversation_manager = ConversationManager()

        # Initialize AI components
        self.ai_gateway = OpenAIGateway()
        self.plan_generator = PlanGenerator(self.ai_gateway)

        # Initialize tool executor
        self.tool_executor = ToolExecutor()

        # Create a headless UI manager (minimal UI for headless mode)
        self.ui_manager = HeadlessUIManager()

        # Initialize real command dispatcher
        self.command_dispatcher = CommandDispatcher(
            ui_manager=self.ui_manager,
            state_manager=self.state_manager,
            session_manager=self.session_manager,
            conversation_manager=self.conversation_manager,
            plan_generator=self.plan_generator,
            tool_executor=self.tool_executor,
        )

        # Set command dispatcher reference in UI manager
        self.ui_manager.set_command_dispatcher(self.command_dispatcher)

        # Event collector for compatibility
        self.event_collector = AsyncMock()

    async def start_session(self, metadata: dict[str, Any] | None = None) -> HeadlessSession:
        """Start a new headless session."""
        # Create session with proper metadata
        import json

        session_metadata = SessionMetadata(
            session_id=f"headless-{int(time.time())}",
            engagement_name="Headless E2E Test",
            current_mode="recon",
            command_history=[],
            notes=json.dumps(metadata) if metadata else None,
            total_commands=0,
            total_hosts_discovered=0,
            total_findings=0,
        )
        # Session is managed by state_manager
        # Initialize state with session metadata
        await self.state_manager.initialize()
        current_state = await self.state_manager.get_current_state()
        current_state.session_metadata = session_metadata

        # Create session wrapper
        session = HeadlessSession(
            session_id=session_metadata.session_id, wish_client=self, metadata=metadata or {}, created_at=time.time()
        )

        self._active_session = session
        logger.info(f"Started headless session {session.session_id}")
        return session

    def on_event(self, event_type: Any) -> Callable[[Callable], Callable]:
        """Register event handler decorator."""

        def decorator(func: Callable) -> Callable:
            # Convert EventType enum to string
            key = event_type.value if hasattr(event_type, "value") else str(event_type)
            if key not in self._event_handlers:
                self._event_handlers[key] = []
            self._event_handlers[key].append(func)
            return func

        return decorator

    async def _send_prompt(self, session_id: str, prompt: str) -> PromptResult:
        """Internal: Send prompt to session."""
        state_before = await self.state_manager.get_current_state()
        # Create a deep copy to avoid mutation issues
        import copy

        state_before = copy.deepcopy(state_before)

        start_time = time.time()

        # Always use real command dispatcher
        try:
            # Initialize command dispatcher session if needed
            if not hasattr(self.command_dispatcher, "current_session"):
                current_state = await self.state_manager.get_current_state()
                session_metadata = current_state.session_metadata
                await self.command_dispatcher.initialize(session_metadata)

            # Clear the log start position for this command
            if hasattr(self.ui_manager, "_command_log_start"):
                self.ui_manager._command_log_start = len(self.ui_manager.logs)

            # Process command through real dispatcher
            success = await self.command_dispatcher.process_command(prompt)

            # Get only the latest result from UI logs
            result_messages = []
            if hasattr(self.ui_manager, "logs"):
                # Get logs from this command only
                log_start = getattr(self.ui_manager, "_command_log_start", 0)
                current_logs = self.ui_manager.logs[log_start:]

                for _log_type, message in current_logs:
                    if isinstance(message, str):
                        result_messages.append(message)

            result = (
                "\n".join(result_messages)
                if result_messages
                else ("Command executed successfully" if success else "Command execution failed")
            )

            execution_time = time.time() - start_time
            state_after = await self.state_manager.get_current_state()

            # Add command to history if method exists
            if hasattr(self.state_manager, "add_command_to_history"):
                await self.state_manager.add_command_to_history(prompt)

            # Fire state changed event
            from .events import EventType

            await self._fire_event(EventType.STATE_CHANGED.value, {"state": state_after, "prompt": prompt})

            # Fire error event for error conditions
            if "failed" in result.lower() or "unreachable" in result.lower() or "error" in result.lower():
                await self._fire_event(
                    EventType.ERROR_OCCURRED.value, {"error": result, "prompt": prompt, "timestamp": time.time()}
                )

            return PromptResult(
                prompt=prompt,
                result=result,
                state_before=state_before,
                state_after=state_after,
                execution_time=execution_time,
            )
        except Exception as e:
            logger.error(f"Error processing command: {e}", exc_info=True)
            execution_time = time.time() - start_time
            state_after = await self.state_manager.get_current_state()

            # Fire error event
            from .events import EventType

            await self._fire_event(
                EventType.ERROR_OCCURRED.value,
                {"error": str(e), "prompt": prompt, "timestamp": time.time()},
            )

            return PromptResult(
                prompt=prompt,
                result=f"Error: {str(e)}",
                state_before=state_before,
                state_after=state_after,
                execution_time=execution_time,
            )

    async def _get_state(self) -> EngagementState:
        """Internal: Get current state."""
        return await self.state_manager.get_current_state()

    async def _end_session(self, session_id: str) -> SessionSummary:
        """Internal: End session."""
        if not self._active_session:
            raise ValueError("No active session")

        duration = time.time() - self._active_session.created_at
        current_state = await self.state_manager.get_current_state()

        # Save session
        await self.session_manager.save_session(current_state)

        # Create summary (use actual command history from state)
        command_count = len(current_state.session_metadata.command_history) if current_state.session_metadata else 0

        summary = SessionSummary(
            session_id=session_id,
            duration=duration,
            prompts_executed=command_count,
            hosts_discovered=len(current_state.hosts) if current_state.hosts else 0,
            findings=len(current_state.findings) if current_state.findings else 0,
        )

        self._active_session = None
        logger.info(f"Ended session {session_id}, duration: {duration:.2f}s")
        return summary

    async def _fire_event(self, event_type: str, data: dict) -> str:
        """Fire event to registered handlers."""
        if event_type in self._event_handlers:
            # Create simple event object
            event = type("Event", (), {"event_type": event_type, "data": data, "timestamp": time.time()})()

            # Call all handlers
            for handler in self._event_handlers[event_type]:
                try:
                    result = await handler(event)
                    # Store result if it's a plan approval
                    if event_type == "plan_approval_required" and result:
                        event.approval_result = result
                        # Handle rejection - if plan is rejected, don't continue execution
                        if result == "reject":
                            return "rejected"
                except Exception as e:
                    logger.error(f"Error in event handler: {e}")
                    import traceback

                    traceback.print_exc()

        return "approved"

    async def cleanup(self) -> None:
        """Cleanup all resources and background tasks."""
        logger.info("Starting HeadlessWish cleanup")

        # 1. Cleanup UI manager jobs
        if hasattr(self.ui_manager, "job_manager"):
            # Cancel all running jobs
            running_jobs = list(self.ui_manager.job_manager.jobs.keys())
            for job_id in running_jobs:
                try:
                    await self.ui_manager.job_manager.cancel_job(job_id)
                except Exception as e:
                    logger.debug(f"Error canceling job {job_id}: {e}")

            # Wait for jobs to finish with longer timeout
            await asyncio.sleep(1.0)

        # 2. Cleanup command dispatcher
        if hasattr(self, "command_dispatcher"):
            # Cancel any pending tasks
            if hasattr(self.command_dispatcher, "_background_tasks"):
                for task in self.command_dispatcher._background_tasks:
                    if not task.done():
                        task.cancel()
                        try:
                            await task
                        except (asyncio.CancelledError, Exception) as e:
                            logger.debug(f"Task cancellation: {e}")

        # 3. Cleanup AI gateway (OpenAI client)
        if hasattr(self, "ai_gateway"):
            try:
                # Use the close method we just added
                if hasattr(self.ai_gateway, "close"):
                    await self.ai_gateway.close()
            except Exception as e:
                logger.debug(f"Error closing AI gateway client: {e}")

        # 4. Wait for subprocess cleanup
        await asyncio.sleep(1.0)

        # 5. Cleanup all pending asyncio tasks
        current_task = asyncio.current_task()
        all_tasks = [t for t in asyncio.all_tasks() if t != current_task and not t.done()]

        if all_tasks:
            logger.info(f"Canceling {len(all_tasks)} pending tasks")
            for task in all_tasks:
                task.cancel()

            # Wait for cancellation to complete with timeout
            try:
                await asyncio.wait_for(asyncio.gather(*all_tasks, return_exceptions=True), timeout=2.0)
            except TimeoutError:
                logger.warning("Some tasks did not complete within timeout")

        # 6. Final sleep to ensure all cleanup is done
        await asyncio.sleep(0.5)

        logger.info("HeadlessWish cleanup completed")
