"""Entry point for the wish shell."""

import argparse
import sys
import asyncio
from wish_sh.wish_tui import main as tui_main
from wish_command_execution.backend import BashConfig, SliverConfig
from sliver import SliverClient, SliverClientConfig


async def check_sliver_sessions(config_path):
    """Check Sliver sessions and return appropriate session ID.
    
    Returns the session ID if only one session exists.
    Displays a list of sessions and returns None if multiple sessions exist.
    Displays an error message and returns None if no sessions exist.
    
    Args:
        config_path: Path to the Sliver client configuration file.
        
    Returns:
        The session ID if only one session exists, None otherwise.
    """
    try:
        # Load client configuration from file
        config = SliverClientConfig.parse_config_file(config_path)
        client = SliverClient(config)
        
        # Connect to server
        await client.connect()
        
        # Get session list
        sessions = await client.sessions()
        
        # Close connection
        await client.close()
        
        if not sessions:
            print("Error: No active Sliver sessions available.")
            return None
        
        if len(sessions) == 1:
            # Automatically select if only one session exists
            return sessions[0].ID
        
        # Display list if multiple sessions exist
        print("Multiple Sliver sessions found. Please specify one with --sliver-session:")
        for i, session in enumerate(sessions):
            print(f"  [{i+1}] ID: {session.ID}")
            print(f"      Name: {session.Name}")
            print(f"      Hostname: {session.Hostname}")
            print(f"      Username: {session.Username}")
            print(f"      OS: {session.OS} {session.Arch}")
            print(f"      Remote Address: {session.RemoteAddress}")
            print()
        
        return None
        
    except Exception as e:
        print(f"Error connecting to Sliver server: {str(e)}")
        return None


def main():
    """Entry point for the wish shell."""
    parser = argparse.ArgumentParser(description="wish - LLM-assisted shell for penetration testing")
    
    # Sliver C2 related arguments
    parser.add_argument("--sliver-config", help="Path to Sliver client config file")
    parser.add_argument("--sliver-session", help="Sliver C2 session ID (optional if only one session exists)")
    
    args = parser.parse_args()
    
    # Create backend configuration
    if args.sliver_config:
        # Handle Sliver session
        if not args.sliver_session:
            # If session ID is not specified, check available sessions
            session_id = asyncio.run(check_sliver_sessions(args.sliver_config))
            if not session_id:
                # Exit if multiple sessions or no sessions found
                return
        else:
            session_id = args.sliver_session
            
        backend_config = SliverConfig(
            session_id=session_id,
            client_config_path=args.sliver_config
        )
    else:
        backend_config = BashConfig()
    
    # Launch TUI
    tui_main(backend_config)


if __name__ == "__main__":
    main()
