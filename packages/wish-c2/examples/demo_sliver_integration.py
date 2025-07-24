#!/usr/bin/env python
"""Demo script for Sliver C2 integration with wish.

This demonstrates various modes of operation:
1. Mock mode - for demos and testing
2. Real mode - actual Sliver server integration
3. Safe mode - security-restricted execution
"""

import asyncio
import sys
from pathlib import Path

# Add parent directory to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from wish_c2 import create_c2_connector, get_c2_connector_from_config
from wish_c2.exceptions import SecurityError


async def demo_mock_mode():
    """Demonstrate mock mode for testing and demos."""
    print("\n=== Mock Mode Demo ===")
    print("Creating mock Sliver connector...")

    connector = create_c2_connector("sliver", mode="mock", config={"demo_mode": True})

    # Connect
    await connector.connect()
    print(f"Connected to mock server at {connector.server}")

    # Get sessions
    sessions = await connector.get_sessions()
    print(f"\nFound {len(sessions)} active sessions:")

    for session in sessions:
        print(f"  - {session.name} ({session.id[:8]}...)")
        print(f"    Host: {session.host} ({session.os}/{session.arch})")
        print(f"    User: {session.user}")
        print(f"    Status: {session.status}")

    # Execute commands
    if sessions:
        session = sessions[0]
        print(f"\nExecuting commands on {session.name}:")

        commands = ["whoami", "pwd", "ls", "id"]
        for cmd in commands:
            result = await connector.execute_command(session.id, cmd)
            print(f"  $ {cmd}")
            print(f"    {result.stdout.strip()}")

    # Disconnect
    await connector.disconnect()
    print("\nDisconnected from mock server")


async def demo_safe_mode():
    """Demonstrate safe mode with security restrictions."""
    print("\n=== Safe Mode Demo ===")
    print("Creating safe Sliver connector with restrictions...")

    # This would normally use real mode, but we use mock for demo
    connector = create_c2_connector(
        "sliver",
        mode="mock",
        config={
            "demo_mode": True,
            "safety": {
                "sandbox_mode": True,
                "read_only": True,
                "allowed_commands": ["ls", "pwd", "whoami", "id"],
                "blocked_paths": ["/etc/shadow", "/etc/passwd"],
            },
        },
    )

    await connector.connect()
    sessions = await connector.get_sessions()

    if sessions:
        session = sessions[0]
        print(f"\nTesting security restrictions on {session.name}:")

        # Test allowed command
        print("\n1. Allowed command (whoami):")
        try:
            result = await connector.execute_command(session.id, "whoami")
            print(f"   Success: {result.stdout.strip()}")
        except SecurityError as e:
            print(f"   Blocked: {e}")

        # Test blocked command (would be blocked in real safe mode)
        print("\n2. Dangerous command (rm -rf /):")
        print("   Would be blocked: Dangerous command pattern detected")

        # Test write command in read-only mode
        print("\n3. Write command in read-only mode (touch test.txt):")
        print("   Would be blocked: Write operations not allowed in read-only mode")

    await connector.disconnect()


async def demo_config_based():
    """Demonstrate configuration-based connector creation."""
    print("\n=== Configuration-Based Demo ===")
    print("Creating connector from configuration...")

    # Example configuration
    config = {
        "c2": {
            "sliver": {
                "enabled": True,
                "mode": "mock",  # Would be "real" in production
                "mock": {"demo_mode": True},
            }
        }
    }

    connector = get_c2_connector_from_config(config)

    if connector:
        await connector.connect()
        print(f"Connected using config-based setup: {connector.server}")

        sessions = await connector.get_sessions()
        print(f"Sessions available: {len(sessions)}")

        await connector.disconnect()
    else:
        print("C2 is disabled in configuration")


async def demo_interactive_shell():
    """Demonstrate interactive shell functionality."""
    print("\n=== Interactive Shell Demo ===")

    connector = create_c2_connector("sliver", mode="mock")
    await connector.connect()

    sessions = await connector.get_sessions()
    if sessions:
        session = sessions[0]
        print(f"Starting interactive shell on {session.name}...")

        shell = await connector.start_interactive_shell(session.id)
        print(f"Shell active: {shell.active}")

        # Execute commands in shell
        commands = ["pwd", "ls -la", "whoami"]
        for cmd in commands:
            print(f"\nshell> {cmd}")
            output = await shell.execute(cmd)
            print(output.strip())

        # Close shell
        await shell.close()
        print("\nShell closed")

    await connector.disconnect()


async def main():
    """Run all demos."""
    print("=== Sliver C2 Integration Demo ===")
    print("This demonstrates the wish C2 connector capabilities")

    try:
        # Run demos
        await demo_mock_mode()
        await demo_safe_mode()
        await demo_config_based()
        await demo_interactive_shell()

        print("\n=== Demo Complete ===")
        print("\nKey Features Demonstrated:")
        print("- Mock mode for testing and demos")
        print("- Security restrictions in safe mode")
        print("- Configuration-based setup")
        print("- Interactive shell sessions")
        print("- Async/await patterns for C2 operations")

    except Exception as e:
        print(f"\nError during demo: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
