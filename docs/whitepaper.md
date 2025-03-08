# wish: Your Wish, Our Command

## 1. Introduction

### 1.1 Purpose of this Document

This whitepaper presents "wish," an AI-powered penetration testing assistant tool, as a submission for the Black Hat Arsenal. The document outlines the tool's capabilities, architecture, and potential applications in offensive security operations.

### 1.2 Background and Objectives

Penetration testing requires extensive knowledge of various tools, commands, and techniques. Even experienced professionals face challenges in remembering specific command syntax or identifying the most efficient approach for a given scenario. 

wish was developed as a component of the RapidPen project, specifically focusing on the "Act" portion of the RapidPen architecture. The tool leverages AI to bridge the gap between natural language instructions and executable commands, enabling both novice and experienced penetration testers to work more efficiently.

![RapidPen Architecture Overview](whitepaper/RapidPen-Architecture-Overview.svg)

The primary objectives of wish are:
- Reduce cognitive load by translating natural language into executable commands
- Accelerate penetration testing workflows through parallel command execution
- Provide contextually relevant command suggestions based on specialized knowledge bases
- Enable seamless operation in both local and compromised environments

## 2. Tool Overview

### 2.1 Key Features

- **Natural Language Command Generation**: Translate user "wishes" into executable shell commands
- **Offensive Security-Focused RAG**: Utilize Retrieval-Augmented Generation with specialized knowledge bases
- **Parallel Command Execution**: Execute and track multiple commands simultaneously
- **Log Analysis and Summarization**: Automatically analyze and summarize command outputs
- **C2 Integration**: Operate within compromised environments through Sliver C2 integration

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

wish can be integrated with Sliver C2 to operate within compromised environments:

TODO: Add details on Sliver C2 integration, command execution in compromised environments, and practical usage scenarios

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
- Additional extension capabilities
- Improvements based on community feedback

## 6. References

TODO: Add relevant research papers, open-source projects used, and reference tools

## Comparison with Similar Tools

| Feature/Characteristic | wish | shell_gpt | nebula |
|----------|------|-----------|--------|
| **Primary Purpose** | Penetration testing assistance | General shell command assistance | Penetration testing assistance |
| **Specialization** | Offensive security | General-purpose | Offensive security |
| **Command Generation** | Multiple parallel commands | Single command (sequential possible) | Multiple commands |
| **Knowledge Base** | Offensive security-focused RAG | None | Internet search & local knowledge base |
| **Model** | OpenAI API (gpt-4o) | OpenAI API | Local models only |
| **Hardware Requirements** | No GPU required | No GPU required | GPU recommended (required) |
| **Use in Compromised Environments** | Possible (C2 integration) | Not possible | Not possible |
| **Log Analysis** | Yes (LLM-based summary & classification) | No | Yes |
| **UI** | TUI | CLI | CLI |
| **Offline Operation** | Partial (API connection required) | Partial (API connection required) | Fully offline |
| **Extensibility** | High (modular structure) | Medium | Medium |

This comparison highlights wish's unique advantages, particularly its offensive security-focused RAG, ability to operate in compromised environments, and no GPU requirement for operation.
