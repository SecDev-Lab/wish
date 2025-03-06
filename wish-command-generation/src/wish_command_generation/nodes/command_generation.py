"""Command generation node functions for the command generation graph."""

from typing import Dict, List, Any

from wish_models.command_result import CommandInput
from ..models import GraphState


def generate_commands(state: GraphState) -> GraphState:
    """Generate commands from Wish"""
    # Mock implementation for testing
    # In the actual implementation, LangChain will be used to generate commands
    
    # Generate simple commands based on the task
    task = state.wish.wish.lower()
    command_inputs = []
    
    if "port scan" in task:
        # Generate port scan commands
        if "10.10.10.123" in task:
            command_inputs = [
                CommandInput(command="nmap -p 1-1000 10.10.10.123", timeout_sec=30),
                CommandInput(command="rustscan -a 10.10.10.123 -- -sV", timeout_sec=60)
            ]
        else:
            # Generate generic commands if no IP address is specified
            command_inputs = [
                CommandInput(command="nmap -p 1-1000 [TARGET_IP]", timeout_sec=30),
                CommandInput(command="rustscan -a [TARGET_IP] -- -sV", timeout_sec=60)
            ]
    elif "vulnerability" in task:
        # Generate vulnerability scan commands
        command_inputs = [
            CommandInput(command="nikto -h [TARGET_IP]", timeout_sec=120),
            CommandInput(command="nmap -sV --script vuln [TARGET_IP]", timeout_sec=180)
        ]
    else:
        # Generate default commands
        command_inputs = [
            CommandInput(command="nmap -sC -sV [TARGET_IP]", timeout_sec=60),
            CommandInput(command="dirb http://[TARGET_IP]/ /usr/share/dirb/wordlists/common.txt", timeout_sec=120)
        ]
    
    # Update the state
    state_dict = state.model_dump()
    state_dict["command_inputs"] = command_inputs
    
    return GraphState(**state_dict)
