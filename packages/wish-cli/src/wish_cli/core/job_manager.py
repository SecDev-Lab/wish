"""Job management system for parallel task execution."""

import asyncio
import logging
import threading
import time
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class JobStatus(Enum):
    """Job status enumeration."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class JobInfo:
    """Job information container."""

    job_id: str
    description: str
    status: JobStatus = JobStatus.PENDING
    created_at: float = field(default_factory=time.time)
    started_at: float | None = None
    completed_at: float | None = None
    result: Any | None = None
    error: str | None = None
    task: asyncio.Task | None = None
    # Extended job information
    command: str | None = None
    tool_name: str | None = None
    parameters: dict[str, Any] | None = None
    output: str | None = None  # Truncated output for display
    full_output: str | None = None  # Complete output for logs
    exit_code: int | None = None
    step_info: dict[str, Any] | None = None  # Original PlanStep information


class JobManager:
    """Manages background jobs with true async execution."""

    def __init__(self, max_concurrent_jobs: int = 10):
        self.max_concurrent_jobs = max_concurrent_jobs
        self.jobs: dict[str, JobInfo] = {}
        self.running_jobs: set[str] = set()
        self._job_counter = 0
        self._job_counter_lock = threading.Lock()
        self._shutdown_event = asyncio.Event()
        self._completion_callbacks: dict[str, list[Callable[[str, JobInfo], None]]] = {}
        logger.info(f"JobManager initialized with max_concurrent_jobs={max_concurrent_jobs}")

    def generate_job_id(self) -> str:
        """Generate unique job ID with thread safety."""
        with self._job_counter_lock:
            self._job_counter += 1
            return f"job_{self._job_counter:03d}"

    async def start_job(
        self,
        job_coroutine: Awaitable[Any],
        description: str,
        job_id: str | None = None,
        completion_callback: Callable[[str, JobInfo], None] | None = None,
        command: str | None = None,
        tool_name: str | None = None,
        parameters: dict[str, Any] | None = None,
        step_info: dict[str, Any] | None = None,
    ) -> str:
        """Start a new background job with extended information."""
        if job_id is None:
            job_id = self.generate_job_id()

        if job_id in self.jobs:
            raise ValueError(f"Job {job_id} already exists")

        # Check concurrent job limit
        if len(self.running_jobs) >= self.max_concurrent_jobs:
            logger.warning(f"Maximum concurrent jobs ({self.max_concurrent_jobs}) reached")
            # Could implement queuing here if needed
            raise RuntimeError(f"Maximum concurrent jobs ({self.max_concurrent_jobs}) reached")

        # Create job info with extended information
        job_info = JobInfo(
            job_id=job_id,
            description=description,
            command=command,
            tool_name=tool_name,
            parameters=parameters,
            step_info=step_info,
        )
        self.jobs[job_id] = job_info

        # Register completion callback
        if completion_callback:
            if job_id not in self._completion_callbacks:
                self._completion_callbacks[job_id] = []
            self._completion_callbacks[job_id].append(completion_callback)

        # Start the job task
        task = asyncio.create_task(self._execute_job(job_id, job_coroutine))
        job_info.task = task
        job_info.status = JobStatus.RUNNING
        job_info.started_at = time.time()
        self.running_jobs.add(job_id)

        logger.info(f"Started job {job_id}: {description} (tool: {tool_name})")
        return job_id

    async def _execute_job(self, job_id: str, job_coroutine: Awaitable[Any]) -> None:
        """Execute job coroutine and handle completion."""
        job_info = self.jobs[job_id]

        try:
            logger.debug(f"Executing job {job_id}")
            result = await job_coroutine

            # Job completed successfully
            job_info.status = JobStatus.COMPLETED
            job_info.result = result
            job_info.completed_at = time.time()

            # Extract output information from result
            if isinstance(result, dict):
                if "output" in result:
                    job_info.full_output = str(result["output"])
                    # Truncate for display (first 50 lines)
                    lines = job_info.full_output.split("\n")
                    if len(lines) > 50:
                        job_info.output = "\n".join(lines[:50]) + f"\n... (truncated, {len(lines)} total lines)"
                    else:
                        job_info.output = job_info.full_output

                if "exit_code" in result:
                    job_info.exit_code = result["exit_code"]
                elif "success" in result:
                    job_info.exit_code = 0 if result["success"] else 1
            elif hasattr(result, "stdout"):
                # Handle ToolExecutor results
                job_info.full_output = str(result.stdout) if result.stdout else ""
                lines = job_info.full_output.split("\n")
                if len(lines) > 50:
                    job_info.output = "\n".join(lines[:50]) + f"\n... (truncated, {len(lines)} total lines)"
                else:
                    job_info.output = job_info.full_output
                job_info.exit_code = 0 if result.success else 1

            # Check for failure patterns in output
            failure_detected = self._detect_failure_in_output(job_info)
            if failure_detected:
                job_info.status = JobStatus.FAILED
                # Extract specific failure reason
                if not job_info.error:
                    job_info.error = self._extract_failure_reason(job_info)
                logger.info(f"Job {job_id} failed based on output analysis: {job_info.error}")
            else:
                logger.info(f"Job {job_id} completed successfully")

        except asyncio.CancelledError:
            # Job was cancelled
            job_info.status = JobStatus.CANCELLED
            job_info.completed_at = time.time()
            logger.info(f"Job {job_id} was cancelled")

        except Exception as e:
            # Job failed with exception
            job_info.status = JobStatus.FAILED
            job_info.error = str(e)
            job_info.completed_at = time.time()
            logger.error(f"Job {job_id} failed: {e}")

        finally:
            # Remove from running jobs
            self.running_jobs.discard(job_id)

            # Call completion callbacks
            if job_id in self._completion_callbacks:
                for callback in self._completion_callbacks[job_id]:
                    try:
                        callback(job_id, job_info)
                    except Exception as e:
                        logger.error(f"Error in completion callback for job {job_id}: {e}")
                # Remove callbacks after calling them
                del self._completion_callbacks[job_id]

    async def cancel_job(self, job_id: str) -> bool:
        """Cancel a running job."""
        if job_id not in self.jobs:
            logger.warning(f"Job {job_id} not found")
            return False

        job_info = self.jobs[job_id]

        if job_info.status != JobStatus.RUNNING:
            logger.warning(f"Job {job_id} is not running (status: {job_info.status})")
            return False

        if job_info.task and not job_info.task.done():
            job_info.task.cancel()
            logger.info(f"Cancelled job {job_id}")
            return True

        return False

    def get_job_status(self, job_id: str) -> JobStatus | None:
        """Get job status."""
        job_info = self.jobs.get(job_id)
        return job_info.status if job_info else None

    def get_job_info(self, job_id: str) -> JobInfo | None:
        """Get complete job information."""
        return self.jobs.get(job_id)

    def list_jobs(self, status_filter: JobStatus | None = None) -> list[JobInfo]:
        """List all jobs, optionally filtered by status."""
        jobs = list(self.jobs.values())
        if status_filter:
            jobs = [job for job in jobs if job.status == status_filter]
        return jobs

    def get_running_jobs(self) -> list[str]:
        """Get list of currently running job IDs."""
        return list(self.running_jobs)

    def get_job_count(self) -> dict[str, int]:
        """Get count of jobs by status."""
        counts = {status.value: 0 for status in JobStatus}
        for job in self.jobs.values():
            counts[job.status.value] += 1
        return counts

    async def wait_for_job(self, job_id: str, timeout: float | None = None) -> JobInfo | None:
        """Wait for a specific job to complete."""
        if job_id not in self.jobs:
            return None

        job_info = self.jobs[job_id]

        if job_info.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]:
            return job_info

        if not job_info.task:
            logger.warning(f"Job {job_id} has no task")
            return job_info

        try:
            if timeout:
                await asyncio.wait_for(job_info.task, timeout=timeout)
            else:
                await job_info.task
        except TimeoutError:
            logger.warning(f"Timeout waiting for job {job_id}")
        except asyncio.CancelledError:
            logger.info(f"Wait cancelled for job {job_id}")

        return job_info

    async def wait_for_all_jobs(self, timeout: float | None = None) -> None:
        """Wait for all running jobs to complete."""
        if not self.running_jobs:
            return

        tasks = []
        for job_id in list(self.running_jobs):
            job_info = self.jobs.get(job_id)
            if job_info and job_info.task:
                tasks.append(job_info.task)

        if not tasks:
            return

        try:
            if timeout:
                await asyncio.wait_for(asyncio.gather(*tasks, return_exceptions=True), timeout=timeout)
            else:
                await asyncio.gather(*tasks, return_exceptions=True)
        except TimeoutError:
            logger.warning(f"Timeout waiting for {len(tasks)} jobs")

    async def cancel_all_jobs(self) -> int:
        """Cancel all running jobs."""
        cancelled_count = 0
        for job_id in list(self.running_jobs):
            if await self.cancel_job(job_id):
                cancelled_count += 1
        return cancelled_count

    def cleanup_completed_jobs(self, max_age_seconds: float = 3600) -> int:
        """Clean up old completed jobs."""
        current_time = time.time()
        to_remove = []

        for job_id, job_info in self.jobs.items():
            if (
                job_info.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]
                and job_info.completed_at
                and current_time - job_info.completed_at > max_age_seconds
            ):
                to_remove.append(job_id)

        for job_id in to_remove:
            del self.jobs[job_id]
            # Also clean up any remaining callbacks
            self._completion_callbacks.pop(job_id, None)

        if to_remove:
            logger.info(f"Cleaned up {len(to_remove)} old jobs")

        return len(to_remove)

    async def shutdown(self) -> None:
        """Shutdown job manager and cancel all running jobs."""
        logger.info("Shutting down JobManager...")

        # Cancel all running jobs
        cancelled_count = await self.cancel_all_jobs()
        if cancelled_count > 0:
            logger.info(f"Cancelled {cancelled_count} running jobs")

        # Wait a bit for cancellations to complete
        if self.running_jobs:
            await asyncio.sleep(0.1)

        # Force cleanup
        self.running_jobs.clear()
        self._completion_callbacks.clear()

        self._shutdown_event.set()
        logger.info("JobManager shutdown complete")

    def _detect_failure_in_output(self, job_info: JobInfo) -> bool:
        """Detect failure patterns in job output based on tool type."""
        if not job_info.full_output:
            return False

        output_lower = job_info.full_output.lower()

        # Common failure patterns
        common_failures = [
            "error:",
            "failed:",
            "failure:",
            "permission denied",
            "connection refused",
            "no such file or directory",
            "command not found",
        ]

        # Tool-specific failure patterns
        tool_specific_failures = {
            "metasploit": [
                "exploit completed, but no session was created",
                "exploit aborted",
                "exploit failed",
                "no session was created",
                "handler failed to bind",
                "connection timed out",
            ],
            "msfconsole": [
                "exploit completed, but no session was created",
                "exploit aborted",
                "exploit failed",
                "no session was created",
            ],
            "nmap": [
                "failed to resolve",
                "host seems down",
                "no host up",
                "pcap_open_live",
            ],
            "nikto": [
                "0 host(s) tested",
                "error opening",
                "cannot resolve",
            ],
            "sqlmap": [
                "no injectable",
                "unable to connect",
                "connection timed out",
            ],
        }

        # Check common failures
        for pattern in common_failures:
            if pattern in output_lower:
                logger.debug(f"Common failure pattern detected: {pattern}")
                return True

        # Check tool-specific failures
        if job_info.tool_name:
            tool_lower = job_info.tool_name.lower()
            for tool_key, patterns in tool_specific_failures.items():
                if tool_key in tool_lower:
                    for pattern in patterns:
                        if pattern in output_lower:
                            logger.debug(f"Tool-specific failure pattern detected for {tool_key}: {pattern}")
                            return True

        # Check exit code (if non-zero and not already detected)
        if job_info.exit_code and job_info.exit_code != 0:
            logger.debug(f"Non-zero exit code detected: {job_info.exit_code}")
            return True

        return False

    def _extract_failure_reason(self, job_info: JobInfo) -> str:
        """Extract specific failure reason from job output."""
        if not job_info.full_output:
            return "Job failed with no output"

        output_lines = job_info.full_output.split("\n")

        # Tool-specific error extraction patterns
        if job_info.tool_name:
            tool_lower = job_info.tool_name.lower()

            # Metasploit/msfconsole specific
            if "metasploit" in tool_lower or "msfconsole" in tool_lower:
                for line in output_lines:
                    if "Exploit aborted" in line:
                        return line.strip()
                    elif "Exploit completed, but no session was created" in line:
                        return "Exploit completed but no session was created"
                    elif "Exploit failed" in line:
                        return line.strip()
                    elif "Handler failed to bind" in line:
                        return "Handler failed to bind to port"
                    elif "This target is not a vulnerable" in line:
                        return line.strip()

            # Nmap specific
            elif "nmap" in tool_lower:
                for line in output_lines:
                    if "Failed to resolve" in line:
                        return line.strip()
                    elif "Host seems down" in line:
                        return "Target host appears to be down"
                    elif "No host up" in line:
                        return "No hosts were found to be up"

            # Nikto specific
            elif "nikto" in tool_lower:
                for line in output_lines:
                    if "0 host(s) tested" in line:
                        return "No hosts were tested - target may be unreachable"
                    elif "ERROR:" in line:
                        return line.strip()

        # Generic error extraction
        for line in output_lines:
            line_lower = line.lower()
            if any(pattern in line_lower for pattern in ["error:", "failed:", "failure:", "aborted:"]):
                return line.strip()

        # Check exit code
        if job_info.exit_code and job_info.exit_code != 0:
            return f"Process exited with code {job_info.exit_code}"

        # Fallback
        return "Job failed - check output for details"
