# wish-ai

AI-powered plan generation and LLM integration for wish penetration testing platform.

## Overview

The `wish-ai` package provides the core AI functionality for wish, including:

- **LLM Gateway**: Abstraction layer for Large Language Model integrations
- **Plan Generation**: AI-powered penetration testing plan creation
- **Context Building**: Rich context construction for LLM prompts
- **Conversation Management**: Chat history and state management
- **Streaming Support**: Real-time response streaming

## Installation

```bash
pip install wish-ai
```

## Quick Start

### Basic Usage

```python
from wish_ai import OpenAIGateway, PlanGenerator, ContextBuilder
from wish_models import EngagementState, SessionMetadata
from datetime import datetime

# Initialize components
gateway = OpenAIGateway()  # Uses OPENAI_API_KEY env var
generator = PlanGenerator(gateway)
context_builder = ContextBuilder()

# Create engagement state
session = SessionMetadata(session_id="test", created_at=datetime.now())
engagement = EngagementState(name="Test Engagement", session_metadata=session)

# Generate a plan
plan = await generator.generate_plan(
    user_input="Scan the network for vulnerabilities",
    engagement_state=engagement
)

print(f"Generated plan: {plan.description}")
for step in plan.steps:
    print(f"- {step.tool_name}: {step.command}")
```

### Streaming Responses

```python
from wish_ai import OpenAIGateway

gateway = OpenAIGateway()

async for chunk in gateway.stream_response("Explain SQL injection"):
    print(chunk, end="", flush=True)
```

## Configuration

### OpenAI API Key

Set your OpenAI API key using one of these methods:

**Configuration File (Recommended):**
```bash
# Initialize configuration file
wish-ai-validate --init-config

# Set your API key
wish-ai-validate --set-api-key "your-openai-api-key-here"
```

**Environment Variable:**
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

**Direct Parameter:**
```python
gateway = OpenAIGateway(api_key="your-api-key")
```

**Manual Configuration:**
Edit `~/.wish/config.toml`:
```toml
[llm]
api_key = "your-openai-api-key-here"
model = "gpt-4o"
max_tokens = 8000
temperature = 0.1
```

### Model Configuration

```python
gateway = OpenAIGateway(
    model="gpt-4o",           # Model name
    max_tokens=8000,          # Response length limit
    temperature=0.1,          # Creativity (0.0-1.0)
    timeout=60.0             # Request timeout
)
```

### Verifying Setup

To verify your API key is configured correctly:

**Using wish-ai validation tool:**
```bash
# Check environment and validate API key
wish-ai-validate

# Initialize configuration file
wish-ai-validate --init-config

# Set API key in configuration
wish-ai-validate --set-api-key "your-key-here"

# Check only environment configuration
wish-ai-validate --check-env

# Test a specific API key
wish-ai-validate --validate-api --api-key="your-key-here"
```

**Expected output for successful validation:**
```
✅ OpenAI API key is valid and accessible
🤖 Using model: gpt-4o
🎉 All checks passed! wish-ai is ready to use.
```

## Core Components

### LLMGateway

Abstract base class for LLM integrations:

```python
from wish_ai.gateway import LLMGateway, OpenAIGateway

# Use OpenAI implementation
gateway = OpenAIGateway()

# Generate plans
response = await gateway.generate_plan(prompt, context)

# Stream responses
async for chunk in gateway.stream_response(prompt):
    print(chunk)

# Estimate tokens
token_count = gateway.estimate_tokens("Your text here")
```

### PlanGenerator

AI-powered penetration testing plan generation:

```python
from wish_ai.planning import PlanGenerator, Plan, PlanStep

generator = PlanGenerator(gateway)

plan = await generator.generate_plan(
    user_input="Enumerate web services",
    engagement_state=engagement_state
)

# Access plan details
print(f"Plan: {plan.description}")
print(f"Steps: {plan.total_steps}")
print(f"High-risk steps: {len(plan.high_risk_steps)}")

# Execute steps
for step in plan.steps:
    if step.requires_confirmation:
        print(f"⚠️  Confirm execution: {step.command}")
    print(f"Running: {step.tool_name} - {step.purpose}")
```

### ContextBuilder

Rich context construction for LLM prompts:

```python
from wish_ai.context import ContextBuilder

builder = ContextBuilder(max_tokens=8000)

context = await builder.build_context(
    user_input="Scan for vulnerabilities",
    engagement_state=engagement_state,
    conversation_history=chat_history
)

# Context includes:
# - User input and current mode
# - Engagement state summary
# - Knowledge base articles (if retriever configured)
# - Conversation history
```

### ConversationManager

Chat history and conversation management:

```python
from wish_ai.conversation import ConversationManager

manager = ConversationManager(max_messages=100)

# Start new session
manager.start_session("session-1")

# Add messages
manager.add_user_message("Hello, WISH")
manager.add_assistant_message("Hello! How can I help with your pentest?")

# Get context for AI
context = manager.get_context_for_ai(max_messages=10)

# Search conversations
results = manager.search_messages("vulnerability")
```

## Error Handling

The package uses a structured error hierarchy:

```python
from wish_ai.gateway.base import (
    LLMGatewayError,
    LLMAuthenticationError,
    LLMRateLimitError,
    LLMConnectionError
)

try:
    gateway = OpenAIGateway()
    response = await gateway.generate_plan(prompt, context)
except LLMAuthenticationError:
    print("❌ Invalid API key")
except LLMRateLimitError:
    print("⏳ Rate limit exceeded, please wait")
except LLMConnectionError:
    print("🌐 Network connection failed")
except LLMGatewayError as e:
    print(f"❌ LLM error: {e}")
```

## Advanced Usage

### Custom Prompt Templates

```python
from wish_ai.context import PromptTemplates

templates = PromptTemplates()

# Get mode-specific prompts
recon_prompt = templates.get_mode_specific_prompt("recon")
exploit_prompt = templates.get_mode_specific_prompt("exploit")

# Build complete context prompt
prompt = templates.build_context_prompt(
    user_input="Scan for open ports",
    context={"mode": "recon", "targets": ["192.168.1.0/24"]}
)
```

### Knowledge Base Integration

```python
from wish_ai.context import ContextBuilder
from wish_knowledge import Retriever

# Initialize with knowledge retriever
retriever = Retriever()  # From wish-knowledge package
builder = ContextBuilder(retriever=retriever)

# Context will include relevant knowledge base articles
context = await builder.build_context(
    user_input="SQL injection testing",
    engagement_state=engagement_state
)
```

## Development

### Running Tests

```bash
cd packages/wish-ai
uv run pytest -v
```

### Type Checking

```bash
uv run mypy src/wish_ai
```

### Code Formatting

```bash
uv run ruff format .
uv run ruff check --fix .
```

## License

MIT License - see the main project LICENSE file for details.

## Related Packages

- **wish-models**: Core data models and validation
- **wish-core**: Business logic and state management
- **wish-knowledge**: RAG and knowledge base integration
- **wish-tools**: Tool integrations and parsers