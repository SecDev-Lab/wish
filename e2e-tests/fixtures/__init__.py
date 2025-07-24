"""E2E test fixtures and mocks."""

from .data import (
    DANGEROUS_PATTERNS,
    HTB_LAME_SCENARIO,
    MOCK_EXPLOIT_OUTPUT,
    MOCK_GOBUSTER_OUTPUT,
    MOCK_NIKTO_OUTPUT,
    MOCK_NMAP_OUTPUT,
    sample_finding,
    sample_host,
    sample_plan,
)
from .mocks import MockEventCollector, MockLLMService, MockToolExecutor, setup_mocks

# Import live testing utilities conditionally
try:
    from .live import (  # noqa: F401
        USE_LIVE_ENV,
        create_live_headless_wish,
        is_command_safe,
        is_target_allowed,
        verify_htb_connectivity,
    )
    LIVE_TESTING_AVAILABLE = True
except ImportError:
    LIVE_TESTING_AVAILABLE = False
    USE_LIVE_ENV = False

__all__ = [
    "MockLLMService",
    "MockToolExecutor",
    "setup_mocks",
    "MockEventCollector",
    "MOCK_NMAP_OUTPUT",
    "MOCK_NIKTO_OUTPUT",
    "MOCK_GOBUSTER_OUTPUT",
    "MOCK_EXPLOIT_OUTPUT",
    "sample_host",
    "sample_finding",
    "sample_plan",
    "HTB_LAME_SCENARIO",
    "DANGEROUS_PATTERNS",
]

# Add live testing exports if available
if LIVE_TESTING_AVAILABLE:
    __all__.extend([
        "create_live_headless_wish",
        "verify_htb_connectivity",
        "is_target_allowed",
        "is_command_safe",
        "USE_LIVE_ENV",
    ])
