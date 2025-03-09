# LangSmith Integration Guide

This guide explains how to set up and use LangSmith with wish-sh for monitoring, debugging, and optimizing your LLM applications.

## What is LangSmith?

[LangSmith](https://smith.langchain.com/) is a platform developed by LangChain for debugging, testing, evaluating, and monitoring LLM applications. It provides:

- **Tracing**: Visualize the execution of your LLM chains and track inputs/outputs
- **Debugging**: Identify issues in your LLM application workflows
- **Performance Analysis**: Measure latency, token usage, and cost
- **Evaluation**: Compare different prompts and models

## Setup

### 1. Create a LangSmith Account

If you don't already have one, create a LangSmith account at [smith.langchain.com](https://smith.langchain.com/).

### 2. Generate an API Key

1. Log in to your LangSmith account
2. Navigate to the API Keys section
3. Click "Create API Key"
4. Copy the generated API key

### 3. Configure Environment Variables

Add the following environment variables to your `.env` file in the project root directory:

```bash
# LangSmith settings
LANGCHAIN_TRACING_V2=true
LANGCHAIN_ENDPOINT=https://api.smith.langchain.com
LANGCHAIN_API_KEY=your-langsmith-api-key-here
LANGCHAIN_PROJECT=wish
```

> **Important**: Place the `.env` file in the project root directory, not in individual package directories. This ensures all packages can access the same environment variables.
>
> Each package's `settings.py` file has been configured to use an absolute path to find the `.env` file in the project root directory:
>
> ```python
> # Get absolute path to project root
> PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
> ENV_PATH = os.path.join(PROJECT_ROOT, ".env")
>
> # ...
>
> model_config = ConfigDict(
>     env_file=[ENV_PATH, ".env"],
>     env_file_encoding="utf-8",
>     case_sensitive=False,
>     extra="allow"
> )
> ```
>
> This ensures that the `.env` file is found correctly regardless of which directory you run the command from.

You can also set a specific project name for each component:

```bash
LANGCHAIN_PROJECT=wish-command-generation  # For command generation
LANGCHAIN_PROJECT=wish-log-analysis        # For log analysis
```

### 4. Verify Setup

After setting up the environment variables, run wish-sh:

```bash
wish
```

Your LLM interactions will now be traced and sent to LangSmith.

## Using LangSmith

### Viewing Traces

1. Log in to [smith.langchain.com](https://smith.langchain.com/)
2. Navigate to the "Traces" section
3. Filter by project name (e.g., "wish-command-generation" or "wish-log-analysis")
4. Click on any trace to view details

### Understanding Trace Details

Each trace shows:

- **Inputs**: The data provided to each node in the workflow
- **Outputs**: The results from each node
- **Execution Time**: How long each step took
- **Token Usage**: For LLM calls, the number of tokens used
- **Errors**: Any errors that occurred during execution

### Debugging with LangSmith

When you encounter issues with wish-sh:

1. Check the LangSmith traces to see which step failed
2. Examine the inputs and outputs of each step
3. Look for error messages or unexpected outputs
4. Use this information to diagnose and fix the issue

### Performance Optimization

LangSmith helps identify performance bottlenecks:

1. Look for steps with long execution times
2. Check token usage for expensive LLM calls
3. Consider optimizing prompts or using different models for steps that are slow or expensive

## Trace Examples

### Command Generation Trace

The command generation workflow includes:

1. **Query Generation**: Converting the user's wish into a search query
2. **Document Retrieval**: Finding relevant documents using the query
3. **Command Generation**: Creating commands based on the wish and retrieved documents

### Log Analysis Trace

The log analysis workflow includes:

1. **Log Summarization**: Summarizing command execution logs
2. **Command State Classification**: Determining if the command succeeded or failed
3. **Result Combination**: Combining the summary and state into a final result

## Advanced Usage

### Custom Projects

You can create different projects in LangSmith to organize your traces:

```bash
LANGCHAIN_PROJECT=wish-dev      # For development
LANGCHAIN_PROJECT=wish-prod     # For production
LANGCHAIN_PROJECT=wish-testing  # For testing
```

### Feedback API

LangSmith provides a feedback API that allows you to rate the quality of generated commands or log analyses. This can be useful for collecting data to improve your models.

## Troubleshooting

### No Traces Appearing

If traces are not appearing in LangSmith:

1. Verify your API key is correct
2. Check that `LANGCHAIN_TRACING_V2` is set to `true`
3. Ensure you have internet connectivity
4. Look for error messages in the wish-sh logs

### Error: "Failed to initialize LangSmith client"

This error indicates an issue with your LangSmith configuration:

1. Check your API key
2. Verify the endpoint URL
3. Ensure you have internet connectivity

## Conclusion

LangSmith integration provides valuable insights into the operation of wish-sh, helping you debug issues, optimize performance, and understand how the system processes your commands. By analyzing traces, you can identify areas for improvement and ensure your LLM applications are working as expected.
