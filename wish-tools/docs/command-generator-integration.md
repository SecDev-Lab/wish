# Command Generator Integration with Tool Framework

This document outlines how to integrate the wish-tools framework with the existing Command Generator API to enable LLM-driven tool selection and command generation.

## Overview

The integration transforms the command generation flow from:
```
User Query → LLM → Shell Commands
```

To:
```
User Query → LLM → Tool Selection → Capability Selection → Parameter Extraction → Command Generation
```

## Tool Selection Strategy

### 1. **Priority-Based Tool Selection**

The LLM should select tools in this priority order:

1. **Specialized Tools First**: Use dedicated tools when available
2. **Bash as Fallback**: Use bash only when no specialized tool exists

```python
TOOL_PRIORITY = {
    "network_scanning": ["bash"],  # Use bash for nmap commands
    "exploitation": ["msfconsole", "bash"],
    "web_requests": ["bash"],  # Use bash for curl/wget commands
    "file_operations": ["bash"],
    "process_management": ["bash"],
    "log_analysis": ["bash"]
}
```

### 2. **Intent-to-Tool Mapping**

```python
INTENT_MAPPING = {
    # Network operations - using bash for nmap commands
    "port_scan": {
        "primary": ("bash", "execute", {"category": "network"}),
        "fallback": None
    },
    "service_detection": {
        "primary": ("bash", "execute", {"category": "network"}),
        "fallback": None
    },
    "vulnerability_scan": {
        "primary": ("bash", "execute", {"category": "network"}),
        "fallback": None
    },
    
    # Exploitation
    "exploit_target": {
        "primary": ("msfconsole", "exploit"),
        "fallback": ("bash", "execute", {"category": "exploitation"})
    },
    "scan_vulnerabilities": {
        "primary": ("msfconsole", "auxiliary"),
        "fallback": ("bash", "execute", {"category": "network"})
    },
    
    # General operations
    "file_search": {
        "primary": ("bash", "execute", {"category": "file"}),
        "fallback": None
    },
    "process_analysis": {
        "primary": ("bash", "execute", {"category": "process"}),
        "fallback": None
    }
}
```

## LLM Prompt Template

### Enhanced Prompt with Tool Awareness

```
You are a penetration testing assistant. You have access to the following tools:

## Available Tools

### msfconsole (Exploitation Framework)
**Category:** exploitation  
**Description:** Metasploit Framework for exploitation and post-exploitation
**Capabilities:**
- exploit: Run exploit modules against targets
  - Parameters: module (required), rhosts (required), lhost (for reverse), rport, payload, options
- auxiliary: Run auxiliary modules (scanners, fuzzers)
  - Parameters: module (required), rhosts (required), rport, options
- search: Search for modules by name/CVE/platform
  - Parameters: query (required), type (exploit/auxiliary/post)

### bash (Fallback Shell)
**Category:** fallback
**Description:** Universal command execution when specialized tools unavailable
**Capabilities:**
- execute: Run any shell command
  - Parameters: command (required), timeout, category (hint)
- script: Execute custom bash scripts
  - Parameters: script (required), args
- tool_combination: Complex command pipelines
  - Parameters: command (required), description

## Tool Selection Rules

1. **Always prefer specialized tools** over bash when available
2. **Use bash only as fallback** when:
   - No specialized tool exists for the task
   - Need to combine multiple tools with pipes/logic
   - Performing basic system operations

3. **Tool availability check**: Assume all tools are available unless specified otherwise

## Response Format

For each user request, respond with a JSON array of tool commands:

```json
[
  {
    "tool": "tool_name",
    "capability": "capability_name", 
    "parameters": {
      "param1": "value1",
      "param2": "value2"
    },
    "explanation": "Why this tool/capability was chosen",
    "priority": 1
  }
]
```

## Examples

**User:** "Scan all ports on 192.168.1.100 and detect services"

**Response:**
```json
[
  {
    "tool": "bash",
    "capability": "execute",
    "parameters": {
      "command": "nmap -sS -p- 192.168.1.100",
      "category": "network"
    },
    "explanation": "Use nmap via bash for comprehensive port scanning",
    "priority": 1
  },
  {
    "tool": "bash", 
    "capability": "execute",
    "parameters": {
      "command": "nmap -sV 192.168.1.100",
      "category": "network"
    },
    "explanation": "Detect services on target host using nmap",
    "priority": 2
  }
]
```

**User:** "Check if target is vulnerable to EternalBlue"

**Response:**
```json
[
  {
    "tool": "msfconsole",
    "capability": "auxiliary", 
    "parameters": {
      "module": "auxiliary/scanner/smb/smb_ms17_010",
      "rhosts": "{{TARGET_IP}}"
    },
    "explanation": "Use Metasploit auxiliary module to check EternalBlue vulnerability",
    "priority": 1
  }
]
```

**User:** "Find all configuration files in /etc"

**Response:**
```json
[
  {
    "tool": "bash",
    "capability": "execute",
    "parameters": {
      "command": "find /etc -name '*.conf' -type f 2>/dev/null",
      "category": "file"
    },
    "explanation": "Use bash for file system operations as no specialized tool needed",
    "priority": 1
  }
]
```

Now process the user's request and select appropriate tools and capabilities.
```

## Implementation in Command Generation API

### Modified Command Generation Workflow

```python
# wish-command-generation-api integration
class ToolAwareCommandGenerator:
    def __init__(self):
        self.tool_registry = tool_registry
        self.intent_mapper = IntentMapper()
        
    async def generate_commands(self, query: str, context: dict) -> List[dict]:
        """Generate commands using tool framework."""
        
        # 1. Get available tools
        available_tools = self._get_available_tools()
        
        # 2. Create enhanced prompt with tool metadata
        prompt = self._create_tool_aware_prompt(available_tools, query, context)
        
        # 3. Get LLM response with tool selections
        llm_response = await self._call_llm(prompt)
        
        # 4. Parse and validate tool selections
        tool_commands = self._parse_tool_selections(llm_response)
        
        # 5. Generate actual commands using tool framework
        commands = []
        for tool_cmd in tool_commands:
            try:
                tool = self.tool_registry.get_tool(tool_cmd["tool"])
                command_input = tool.generate_command(
                    capability=tool_cmd["capability"],
                    parameters=tool_cmd["parameters"]
                )
                
                commands.append({
                    "command": command_input.command,
                    "timeout_sec": command_input.timeout_sec,
                    "tool": tool_cmd["tool"],
                    "capability": tool_cmd["capability"],
                    "explanation": tool_cmd.get("explanation", ""),
                    "metadata": {
                        "tool_metadata": tool.metadata.dict(),
                        "parameters": tool_cmd["parameters"]
                    }
                })
            except Exception as e:
                # Fallback to bash if tool command generation fails
                commands.append({
                    "command": f"# Error generating command: {e}",
                    "timeout_sec": 300,
                    "tool": "bash",
                    "capability": "execute",
                    "explanation": f"Fallback due to error: {e}"
                })
        
        return commands
    
    def _get_available_tools(self) -> dict:
        """Get metadata for all available tools."""
        tools_metadata = {}
        for tool_metadata in self.tool_registry.list_tools():
            tools_metadata[tool_metadata.name] = {
                "description": tool_metadata.description,
                "category": tool_metadata.category,
                "capabilities": [
                    {
                        "name": cap.name,
                        "description": cap.description,
                        "parameters": cap.parameters,
                        "examples": cap.examples[:2]  # Limit examples for prompt size
                    }
                    for cap in tool_metadata.capabilities
                ],
                "requirements": tool_metadata.requirements,
                "tags": tool_metadata.tags
            }
        return tools_metadata
    
    def _create_tool_aware_prompt(self, tools: dict, query: str, context: dict) -> str:
        """Create enhanced prompt with tool information."""
        # Build tool descriptions
        tool_descriptions = []
        for tool_name, tool_info in tools.items():
            desc = f"### {tool_name} ({tool_info['category'].title()})\n"
            desc += f"**Description:** {tool_info['description']}\n"
            desc += "**Capabilities:**\n"
            
            for cap in tool_info['capabilities']:
                desc += f"- {cap['name']}: {cap['description']}\n"
                if cap['parameters']:
                    desc += f"  - Parameters: {', '.join(cap['parameters'].keys())}\n"
            
            tool_descriptions.append(desc)
        
        # Build context information
        context_info = []
        if context.get('target_host'):
            context_info.append(f"Target Host: {context['target_host']}")
        if context.get('current_directory'):
            context_info.append(f"Current Directory: {context['current_directory']}")
        
        prompt = f"""You are a penetration testing assistant with access to specialized tools.

## Available Tools

{chr(10).join(tool_descriptions)}

## Current Context
{chr(10).join(context_info) if context_info else "No specific context provided"}

## Tool Selection Rules
1. Always prefer specialized tools over bash when available
2. Use bash only as fallback when no specialized tool exists
3. Consider tool availability and context

## User Request
{query}

Respond with a JSON array of tool commands using the format specified above.
"""
        return prompt
```

## Migration Strategy

### Phase 1: Parallel Implementation
- Keep existing command generation working
- Add new tool-aware endpoint alongside existing one
- Test with subset of queries

### Phase 2: Gradual Migration  
- Route specific query types to tool-aware generator
- Fallback to legacy generator if tool-aware fails
- Monitor success rates and performance

### Phase 3: Full Replacement
- Replace legacy generator with tool-aware version
- Remove fallback mechanisms
- Optimize for performance

## Benefits

1. **Better Tool Utilization**: LLM chooses optimal tools for each task
2. **Structured Output**: Tools provide metadata and structured results
3. **Safety**: Tool validation prevents dangerous commands
4. **Maintainability**: Adding new tools automatically improves LLM capabilities
5. **Fallback Robustness**: Bash ensures commands can always be generated

## Testing Strategy

### Unit Tests
```python
def test_tool_selection():
    generator = ToolAwareCommandGenerator()
    
    # Test port scanning uses bash for nmap commands
    commands = await generator.generate_commands(
        "scan ports on 192.168.1.1", 
        {"target_host": "192.168.1.1"}
    )
    
    assert commands[0]["tool"] == "bash"
    assert commands[0]["capability"] == "execute"
    assert "nmap" in commands[0]["command"]
    
def test_msfconsole_selection():
    generator = ToolAwareCommandGenerator()
    
    commands = await generator.generate_commands(
        "exploit target with EternalBlue",
        {"target_host": "192.168.1.1"}
    )
    
    assert commands[0]["tool"] == "msfconsole"
    assert commands[0]["capability"] == "exploit"
```

### Integration Tests
- Test with real LLM API calls
- Verify command generation for various scenarios
- Test fallback mechanisms
- Performance benchmarking

This integration maintains backward compatibility while leveraging the full power of the tool framework.