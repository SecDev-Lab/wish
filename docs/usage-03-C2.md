# Command and Control (C2) Integration Guide

This guide explains how to use wish-sh with Command and Control (C2) frameworks, specifically Sliver C2.

## Sliver C2 Integration

wish-sh can connect to a Sliver C2 server to execute commands on compromised systems. This allows you to use the natural language capabilities of wish-sh to control remote systems through Sliver C2.

### Prerequisites

1. A running Sliver C2 server
2. At least one active Sliver session (implant)
3. An operator configuration file

### Setting Up Sliver C2

If you haven't already set up Sliver C2, follow these steps:

1. Install Sliver C2 server:
   ```bash
   sudo apt install sliver
   ```

2. Start the Sliver C2 server:
   ```bash
   sliver-server
   ```

3. Enable multiplayer mode:
   ```
   [server] sliver > multiplayer
   ```

4. Create an operator configuration file:
   ```
   [server] sliver > new-operator --name wish --lhost 127.0.0.1
   ```
   This will create a configuration file (e.g., `wish_127.0.0.1.cfg`) that wish-sh will use to connect to the Sliver server.

5. Generate and deploy a Sliver implant to your target system.

### Using wish-sh with Sliver C2

To use wish-sh with Sliver C2, you need to specify the Sliver configuration file:

```bash
wish --sliver-config /path/to/wish_127.0.0.1.cfg
```

If you have only one active Sliver session, wish-sh will automatically connect to it. If you have multiple sessions, wish-sh will display a list of available sessions and you'll need to specify which one to use:

```bash
wish --sliver-config /path/to/wish_127.0.0.1.cfg --sliver-session SESSION_ID
```

Replace `SESSION_ID` with the ID of the session you want to connect to.

### Example Workflow

1. Start the Sliver server and ensure you have at least one active session.

2. Launch wish-sh with the Sliver configuration:
   ```bash
   wish --sliver-config ~/wish_127.0.0.1.cfg
   ```

3. If you have multiple sessions, wish-sh will display them and exit. Choose the session you want to use and relaunch with the session ID:
   ```bash
   wish --sliver-config ~/wish_127.0.0.1.cfg --sliver-session a3a52b7f-eb9c-410a-b349-c23708e01572
   ```

4. Use wish-sh as you normally would, but now all commands will be executed on the remote system through Sliver C2.

### Example Wishes

Here are some example wishes you can use with the Sliver C2 integration:

- "Show me the current user and privileges on this system"
- "List all running processes"
- "Find all files modified in the last 24 hours"
- "Check if this system is vulnerable to CVE-2023-1234"

### Limitations

- The Sliver C2 integration only supports command execution. Other Sliver features like file transfer, port forwarding, etc. are not currently supported through wish-sh.
- Command execution is synchronous, meaning wish-sh will wait for the command to complete before allowing you to enter another wish.
- Some complex commands that rely on interactive input may not work as expected.

## Future Enhancements

Future versions of wish-sh may include:

- Support for other C2 frameworks (Metasploit, Covenant, etc.)
- Advanced Sliver C2 features like file transfer, port forwarding, etc.
- Multi-session support for controlling multiple compromised systems simultaneously
