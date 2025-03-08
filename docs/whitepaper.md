# wish: Your Wish, Our Command

## 1. Introduction

### 1.1 Purpose of this Document

This whitepaper presents "wish," an AI-powered shell environment specifically designed for penetration testing. Operating as an intelligent command-line interface, wish translates natural language inputs into executable shell commands, providing penetration testers with an intuitive and efficient workflow. The document outlines the tool's capabilities, architecture, and potential applications in offensive security operations.

### 1.2 Background and Objectives

#### Beyond Cheatsheets and Copy-Paste

Penetration testing education and practice, whether for OSCP certification, HackTheBox, TryHackMe, or CTF competitions, has traditionally relied heavily on copying and pasting commands from web pages and cheatsheets. While this approach serves an educational purpose, the emergence of Large Language Models (LLMs) presents an opportunity to make this process significantly more intelligent and efficient.

wish was designed to shift the focus from memorizing commands to developing situational awareness and strategic thinking. By simply expressing what needs to be accomplished as a natural language "wish," penetration testers receive contextually appropriate command suggestions, allowing them to concentrate on the higher-level aspects of security assessment rather than syntax details.

#### Accelerating Attack Vector Exploration

Speed is critical in penetration testing, where multiple attack vectors must often be explored to identify viable entry points. Traditional approaches using terminal multiplexers and manual command management can become cumbersome and time-consuming.

wish addresses this challenge by generating multiple commands simultaneously and executing them in parallel. Commands run in the background, with the system providing interruption notifications upon completion. This parallel processing approach allows penetration testers to continue strategizing while commands execute, significantly accelerating the testing workflow.

#### Enhancing Post-Exploitation Experience

Penetration testing extends beyond initial access to include post-exploitation activities. However, shells obtained during this phase are typically limited in functionality, degrading the tester's experience and efficiency. Traditional post-exploitation workflows often force penetration testers to abandon their preferred tools and adapt to restrictive command-line environments.

wish transforms this experience by bringing its AI-powered shell capabilities directly into compromised environments. By integrating with Command and Control (C2) frameworks, wish enables penetration testers to continue using natural language commands even after successful exploitation. This means the same intuitive interface that translates "wishes" into executable commands on your local machine can now operate within the compromised target system. While the current implementation focuses on Sliver C2 integration, the architecture is designed to support various C2 frameworks, including custom solutions, in the future. This flexible integration approach ensures that penetration testers can maintain their efficient, AI-assisted workflow throughout the entire testing process, from initial reconnaissance to post-exploitation.

#### Part of the RapidPen Ecosystem

wish was developed as a component of the RapidPen project [1], an AI-driven system for automated penetration testing. RapidPen's architecture is divided into two main components: "Re" for task planning and "Act" for command execution. The effectiveness of the Act component significantly influences the success of initial access in the RapidPen system.

By extracting the Act component as an open-source tool, wish aims to refine and improve this critical functionality through community involvement. While RapidPen focuses on automation, wish acknowledges the continued importance of human-led penetration testing and serves as an assistant that enhances human capabilities rather than replacing them.

![RapidPen Architecture Overview](whitepaper/RapidPen-Architecture-Overview.svg)

The primary objectives of wish are:
- Reduce cognitive load by translating natural language into executable commands
- Accelerate penetration testing workflows through parallel command execution
- Provide contextually relevant command suggestions based on specialized knowledge bases
- Enable seamless operation in both local and compromised environments
- Support the evolution of the RapidPen ecosystem while enhancing human-led security testing

## 2. Tool Overview

### 2.1 Key Features

- **Natural Language Command Generation**: Translate user "wishes" into executable shell commands
- **Offensive Security-Focused Knowledge Base**: Utilize specialized knowledge bases tailored for offensive security operations
- **Parallel Command Execution**: Execute and track multiple commands simultaneously
- **Log Analysis and Summarization**: Automatically analyze and summarize command outputs
- **C2 Integration**: Operate within compromised environments through C2 framework integration, currently supporting Sliver C2 with plans for expanded framework support

### 2.2 Use Cases

wish is designed for:
- Professional penetration testers during initial access and post-exploitation phases
- Security students preparing for OSCP, HTB, THM, or CTF (Boot2Root) challenges
- Security researchers exploring new attack vectors

TODO: Add specific use case examples for beginners, intermediate, and advanced users

### 2.3 Architecture

wish consists of six main packages, each with specific responsibilities:

![Logical Architecture](whitepaper/logical-arch.png)

The control and data flow between components is illustrated below:

![Control and Data Flow](whitepaper/control-data-flow.png)

The detailed architecture of the Act component, which forms the basis of wish:

![Act Architecture](whitepaper/Act-Architecture.svg)

**Core Components:**

- **wish-models**: Core data models used throughout the system
- **wish-command-execution**: Handles command execution and status tracking
- **wish-log-analysis**: Analyzes command outputs using LLM
- **wish-command-generation**: Generates commands from natural language using RAG
- **wish-knowledge-loader**: Manages knowledge bases for RAG
- **wish-sh**: Provides the Text-based User Interface (TUI)

## 3. Setup

### 3.1 Requirements

- **Operating System**: Linux (primary), macOS (supported)
- **Python**: Version 3.13+
- **Dependencies**: OpenAI API access, various Python packages
- **API Keys**: OpenAI API key required

TODO: Add detailed hardware requirements and optional dependencies

### 3.2 Installation

TODO: Add step-by-step installation instructions, initial configuration, knowledge base setup, and C2 integration setup

## 4. Usage

### 4.1 Basic Usage

The wish TUI provides an intuitive interface for:
- Entering natural language "wishes"
- Reviewing suggested commands
- Executing commands and monitoring their status
- Analyzing command outputs

TODO: Add detailed usage instructions with screenshots

### 4.2 Leveraging Knowledge Bases

wish utilizes specialized knowledge bases to improve command generation:

TODO: Add information about available knowledge bases, how to add custom knowledge bases, and examples of effective queries

### 4.3 Operating in Compromised Shells

wish can be integrated with Command and Control (C2) frameworks to operate within compromised environments:

TODO: Add details on current Sliver C2 integration, plans for supporting additional C2 frameworks, command execution in compromised environments, and practical usage scenarios

## 5. Development Status

### 5.1 Completed Development

Current capabilities include:
- Functional TUI prototype
- Natural language to command generation
- Multiple command suggestion and execution tracking
- Knowledge base integration from GitHub repositories
- Sliver C2 integration for compromised shell operation
- OpenAI gpt-4o integration

### 5.2 Planned Development (by August 2025)

- Wish History functionality
- Environment-aware command suggestions (OS, available executables, dictionary files)
- Utilization of successful command examples
- Portal interface for C2 setup and knowledge base import

### 5.3 Future Development

- Support for various LLM providers
- Expanded C2 framework integration beyond Sliver C2, including support for custom and proprietary C2 solutions
- Additional extension capabilities
- Improvements based on community feedback

## 6. References

[1] NAKATANI, Sho. RapidPen: Fully Automated IP-to-Shell Penetration Testing with LLM-based Agents. arXiv preprint arXiv:2502.16730, 2025.

TODO: Add additional research papers, open-source projects used, and reference tools

## Comparison with Similar Tools

| Feature/Characteristic | wish | shell_gpt | nebula |
|----------|------|-----------|--------|
| **Primary Purpose** | Penetration testing assistance | General shell command assistance | Penetration testing assistance |
| **Specialization** | Offensive security | General-purpose | Offensive security |
| **Command Generation** | Multiple parallel commands | Single command (sequential possible) | Multiple commands |
| **Knowledge Base** | Offensive security-focused specialized knowledge base | None | Internet search & local knowledge base |
| **Model** | OpenAI API (gpt-4o) | OpenAI API | Local models only |
| **Hardware Requirements** | No GPU required | No GPU required | GPU recommended (required) |
| **Use in Compromised Environments** | Possible (C2 integration) | Not possible | Not possible |
| **Log Analysis** | Yes (LLM-based summary & classification) | No | Yes |
| **UI** | TUI | CLI | CLI |
| **Offline Operation** | Partial (API connection required) | Partial (API connection required) | Fully offline |
| **Extensibility** | High (modular structure) | Medium | Medium |

This comparison highlights wish's unique advantages, particularly its offensive security-focused knowledge base, ability to operate in compromised environments, and no GPU requirement for operation.
