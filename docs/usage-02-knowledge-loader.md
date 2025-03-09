# Knowledge Loader Usage Guide

This guide explains how to use `wish-knowledge-loader` to enhance wish-sh with domain-specific knowledge from GitHub repositories.

## Overview

The wish-knowledge-loader is a tool that allows you to load knowledge bases from GitHub repositories into wish-sh. This knowledge is then used to improve command suggestions through Retrieval-Augmented Generation (RAG).

By loading relevant knowledge bases, you can make wish-sh more effective for specific domains or tasks, such as:

- Penetration testing tools and techniques
- System administration tasks
- Development workflows for specific languages or frameworks
- Cloud infrastructure management

## Prerequisites

Before using wish-knowledge-loader, ensure you have:

1. [Installed wish-sh and wish-knowledge-loader](setup.md)
2. Set up the required environment variables (`OPENAI_API_KEY`, `OPENAI_MODEL`, `WISH_HOME`)

## Loading a Knowledge Base

To load a knowledge base from a GitHub repository, use the following command:

```bash
wish-knowledge-loader --repo-url https://github.com/username/repo --glob "**/*.md" --title "Knowledge Base Title"
```

### Parameters

- `--repo-url`: The URL of the GitHub repository to clone
- `--glob`: A glob pattern that specifies which files to include in the knowledge base (e.g., `"**/*.md"` for all Markdown files)
- `--title`: A descriptive title for the knowledge base

### Example

To load a comprehensive penetration testing knowledge base:

```bash
wish-knowledge-loader --repo-url https://github.com/HackTricks-wiki/hacktricks --glob "**/*.md" --title "HackTricks Wiki"
```

## How It Works

When you run wish-knowledge-loader:

1. It downloads the specified GitHub repository
2. It collects content from files matching the glob pattern
3. It processes and indexes this content
4. It stores the processed information in your `$WISH_HOME` directory
5. wish-command-generation uses this knowledge to suggest better commands

## Using Multiple Knowledge Bases

You can load multiple knowledge bases by running wish-knowledge-loader multiple times with different repositories. Each knowledge base will be stored separately and used by wish-sh when generating commands.

For example:

```bash
# Load HackTricks Wiki knowledge base
wish-knowledge-loader --repo-url https://github.com/HackTricks-wiki/hacktricks --glob "**/*.md" --title "HackTricks Wiki"

# Load OSCP Guide knowledge base
wish-knowledge-loader --repo-url https://github.com/0xsyr0/OSCP --glob "README.md" --title "OSCP Guide"
```

## Verifying Loaded Knowledge Bases

After loading a knowledge base, you can verify that it's being used by wish-sh by:

1. Starting wish-sh
2. Entering a wish related to the knowledge base you loaded
3. Observing the suggested commands, which should now be more accurate and domain-specific

## Example Use Cases

### Penetration Testing

If you've loaded the HackTricks Wiki and OSCP Guide knowledge bases:

```
Wish: Perform a privilege escalation check on a Linux system
```

wish-sh might suggest:

```bash
./linpeas.sh -a | tee linpeas_output.txt
```

### System Administration

If you've loaded a knowledge base about system administration:

```
Wish: Find processes using the most memory and CPU
```

wish-sh might suggest:

```bash
ps aux --sort=-%mem,%cpu | head -n 10
```

## Next Steps

Once you've enhanced wish-sh with relevant knowledge bases, you can:

1. [Explore Command and Control (C2) for Target System Operations](usage-03-C2.md)
2. Create your own knowledge base repositories to share with others
3. Combine multiple knowledge bases for comprehensive command suggestions
