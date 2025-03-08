# Basic Usage Guide

This guide covers the basic usage of `wish-sh`, an LLM-assisted shell that helps users execute commands by translating natural language "wishes" into executable shell commands.

## Starting wish-sh

After [setting up wish-sh](setup.md), you can start it by running:

```bash
wish
```

Or on macOS:

```bash
wish-sh
```

## The wish-sh Interface

When you start wish-sh, you'll see a text-based user interface (TUI) with the following components:

- **Input area**: Where you type your wishes
- **Suggestion area**: Where wish-sh displays suggested commands
- **Execution area**: Where command execution results are displayed
- **Status bar**: Shows the current status and available actions

## Basic Workflow

### 1. Enter Your Wish

Type your wish in natural language in the input area. For example:

```
Find all PDF files in the current directory and its subdirectories
```

Press Enter to submit your wish.

### 2. Review Suggested Commands

wish-sh will process your wish and suggest one or more shell commands that accomplish your task. For example:

```bash
find . -type f -name "*.pdf"
```

Review the suggested commands carefully before proceeding.

### 3. Execute or Reject Commands

- Press `Enter` to execute the suggested command
- Press `Esc` to reject the suggestion and return to the input area

### 4. Monitor Execution

Once you execute a command, wish-sh will display:

- The command being executed
- Real-time output from the command
- Exit code and execution status
- A summary of the command's results

## Example Wishes

Here are some example wishes you can try:

```
List all running processes sorted by memory usage
```

```
Create a backup of all .txt files in a new directory called backups
```

```
Show system information including CPU and memory
```

```
Find all files modified in the last 24 hours
```

## Next Steps

Once you're comfortable with the basic usage of wish-sh, you can enhance its capabilities by:

1. [Loading knowledge bases](usage-02-knowledge-loader.md) to improve command suggestions
2. [Using advanced features](usage-03-C2.md) for more complex tasks
