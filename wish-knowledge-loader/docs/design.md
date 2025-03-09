# wish-knowledge-loader Design

## Overview

wish-knowledge-loader is a tool for creating and managing knowledge bases from GitHub repositories and storing them in a vector database for retrieval.

## Architecture

### Knowledge and Repository Relationship

Knowledge bases and repositories have an N:1 relationship. This means multiple knowledge bases can be created from a single repository.

For example, different file patterns from the same repository can be treated as separate knowledge bases:

- Repository: `github.com/user/repo`
  - Knowledge Base 1: `*.md` (Markdown files)
  - Knowledge Base 2: `*.py` (Python files)
  - Knowledge Base 3: `docs/*.rst` (Documentation files)

This allows managing different parts of the same repository as separate knowledge bases.

### Components

1. **RepoCloner**: Clones GitHub repositories
2. **DocumentLoader**: Loads files and splits them into chunks
3. **VectorStore**: Stores documents in a vector database
4. **KnowledgeMetadata**: Manages knowledge base metadata

### Data Flow

1. Clone repository
2. Load files matching the specified pattern
3. Split documents into chunks
4. Store in vector database
5. Create and save metadata

## CLI Commands

- `wish-knowledge-loader load`: Load a knowledge base
- `wish-knowledge-loader list`: List loaded knowledge bases
- `wish-knowledge-loader delete`: Delete a knowledge base

### Repository Management

When deleting a knowledge base:
- The repository is preserved if other knowledge bases use it
- The repository is only deleted when removing the last knowledge base that uses it
