# wish-knowledge

Knowledge base management and RAG (Retrieval-Augmented Generation) for the wish penetration testing platform.

## Overview

wish-knowledge provides a comprehensive knowledge management system that integrates security knowledge bases like HackTricks into wish. It enables intelligent context-aware suggestions and technique recommendations during penetration testing.

## Key Features

- **Knowledge Base Integration**: Built-in support for HackTricks and custom knowledge sources
- **RAG Implementation**: Retrieval-Augmented Generation for contextual AI responses
- **Vector Search**: Efficient semantic search using embeddings
- **Dynamic Updates**: Automatic knowledge base synchronization
- **Multi-source Support**: Combine multiple knowledge sources

## Installation

```bash
# Install dependencies in development environment
uv sync --dev

# Install as package (future release)
pip install wish-knowledge
```

## Quick Start

### Basic Usage Example

```python
from wish_knowledge import KnowledgeManager, Retriever
from wish_models import SessionMetadata

# Initialize knowledge manager
knowledge_manager = KnowledgeManager()

# Initialize retriever
retriever = Retriever(knowledge_manager)

# Search for relevant knowledge
query = "SQL injection testing web application"
results = await retriever.search(query, top_k=5)

for result in results:
    print(f"Title: {result.title}")
    print(f"Score: {result.relevance_score}")
    print(f"Content: {result.content[:200]}...")
    print("---")

# Get context-aware suggestions
context = {
    "current_mode": "enum",
    "target_type": "web_application",
    "discovered_services": ["http", "https"]
}
suggestions = await retriever.get_contextual_suggestions(context)
```

### Knowledge Base Management

```python
from wish_knowledge import KnowledgeBase, HackTricksLoader

# Load HackTricks knowledge base
hacktricks = HackTricksLoader()
await hacktricks.load()

# Create custom knowledge base
custom_kb = KnowledgeBase(name="Custom Techniques")
custom_kb.add_article(
    title="Advanced SQLi Techniques",
    content="...",
    tags=["sql", "injection", "web"],
    category="exploitation"
)

# Combine knowledge bases
knowledge_manager.add_knowledge_base(hacktricks)
knowledge_manager.add_knowledge_base(custom_kb)
```

## Architecture

### Core Components

#### KnowledgeManager
Central manager for all knowledge bases and indexing.

```python
from wish_knowledge import KnowledgeManager

manager = KnowledgeManager()

# Add knowledge bases
manager.add_knowledge_base(hacktricks_kb)
manager.add_knowledge_base(custom_kb)

# Update indices
await manager.update_indices()

# Get statistics
stats = manager.get_statistics()
print(f"Total articles: {stats.total_articles}")
print(f"Knowledge bases: {stats.knowledge_bases}")
```

#### Retriever
Intelligent retrieval system with RAG capabilities.

```python
from wish_knowledge import Retriever

retriever = Retriever(manager)

# Basic search
results = await retriever.search("privilege escalation linux")

# Filtered search
results = await retriever.search(
    query="web vulnerabilities",
    filters={"category": "web", "tags": ["owasp"]}
)

# Similarity search with embeddings
similar = await retriever.find_similar(article_id="123")
```

#### Embedding System
Vector embeddings for semantic search.

```python
from wish_knowledge.embeddings import EmbeddingGenerator

embedder = EmbeddingGenerator(model="text-embedding-ada-002")

# Generate embeddings
text = "SQL injection vulnerability in login form"
embedding = await embedder.generate(text)

# Batch processing
texts = ["XSS attack", "CSRF protection", "SQLi prevention"]
embeddings = await embedder.generate_batch(texts)
```

## Knowledge Sources

### Built-in Sources

#### HackTricks
- Comprehensive pentesting methodology
- Attack techniques and tools
- Platform-specific guides
- Cloud security techniques

#### OWASP Knowledge
- Web application security
- Top 10 vulnerabilities
- Testing guides
- Cheat sheets

#### Custom Sources
- Internal playbooks
- Team-specific techniques
- Client-specific knowledge
- Historical findings

### Adding Custom Knowledge

```python
from wish_knowledge import KnowledgeBase, Article

# Create knowledge base
kb = KnowledgeBase(name="Team Playbook")

# Add articles programmatically
article = Article(
    title="Internal Network Pentesting Guide",
    content="""
    ## Overview
    This guide covers our standard approach...
    
    ## Methodology
    1. Network discovery
    2. Service enumeration
    ...
    """,
    tags=["internal", "network", "methodology"],
    category="methodology"
)
kb.add_article(article)

# Load from files
kb.load_from_markdown("playbooks/")

# Load from URL
kb.load_from_url("https://example.com/techniques.json")
```

## Search and Retrieval

### Search Options

```python
# Full-text search
results = await retriever.search(
    query="buffer overflow",
    search_type="full_text"
)

# Semantic search
results = await retriever.search(
    query="how to exploit weak authentication",
    search_type="semantic"
)

# Hybrid search (combines full-text and semantic)
results = await retriever.search(
    query="windows privilege escalation",
    search_type="hybrid",
    weights={"full_text": 0.3, "semantic": 0.7}
)
```

### Filtering and Ranking

```python
# Advanced filtering
results = await retriever.search(
    query="exploitation",
    filters={
        "category": ["web", "network"],
        "tags": {"include": ["owasp"], "exclude": ["outdated"]},
        "date_range": {"after": "2023-01-01"}
    },
    sort_by="relevance",
    top_k=10
)

# Custom ranking
def custom_ranker(results):
    # Boost results based on custom criteria
    for result in results:
        if "critical" in result.tags:
            result.score *= 1.5
    return sorted(results, key=lambda x: x.score, reverse=True)

results = await retriever.search(query, ranker=custom_ranker)
```

## Integration with wish-ai

The knowledge system integrates seamlessly with wish-ai for enhanced AI responses:

```python
from wish_ai import ContextBuilder
from wish_knowledge import Retriever

# Configure context builder with retriever
retriever = Retriever()
context_builder = ContextBuilder(retriever=retriever)

# Build context with relevant knowledge
context = await context_builder.build_context(
    user_input="How do I test for SQL injection?",
    engagement_state=engagement_state
)

# Context now includes relevant HackTricks articles
```

## Development Guide

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test file
uv run pytest tests/test_retriever.py

# Run integration tests
uv run pytest tests/integration/
```

### Project Structure

```
packages/wish-knowledge/
├── src/wish_knowledge/
│   ├── __init__.py           # Package exports
│   ├── manager.py            # Knowledge manager
│   ├── retriever.py          # Retrieval system
│   ├── knowledge_base.py     # Base knowledge class
│   ├── loaders/              # Knowledge loaders
│   │   ├── __init__.py
│   │   ├── hacktricks.py
│   │   ├── markdown.py
│   │   └── json.py
│   ├── embeddings/           # Embedding system
│   │   ├── __init__.py
│   │   ├── generator.py
│   │   └── models.py
│   └── search/               # Search implementations
│       ├── __init__.py
│       ├── full_text.py
│       └── semantic.py
├── tests/
│   ├── test_manager.py
│   ├── test_retriever.py
│   └── fixtures/
└── README.md
```

## Configuration

### Knowledge Base Settings

Configure in `~/.wish/config.toml`:

```toml
[knowledge]
# Default search settings
default_top_k = 5
default_search_type = "hybrid"

# Embedding settings
[knowledge.embeddings]
model = "text-embedding-ada-002"
cache_embeddings = true
batch_size = 100

# HackTricks settings
[knowledge.hacktricks]
auto_update = true
update_interval = 86400  # Daily updates
local_path = "~/.wish/knowledge/hacktricks"

# Custom knowledge bases
[knowledge.custom]
paths = [
    "~/pentest-playbooks",
    "/opt/wish/knowledge"
]
```

### Performance Optimization

```toml
[knowledge.performance]
# Index settings
index_type = "faiss"  # or "annoy", "simple"
index_threads = 4

# Cache settings
cache_size_mb = 512
cache_ttl_seconds = 3600

# Search optimization
max_results_per_source = 100
parallel_search = true
```

## API Reference

### KnowledgeManager

- `add_knowledge_base(kb)`: Add a knowledge base
- `remove_knowledge_base(name)`: Remove a knowledge base
- `update_indices()`: Update search indices
- `get_statistics()`: Get knowledge base statistics
- `clear_cache()`: Clear search cache

### Retriever

- `search(query, **kwargs)`: Search across knowledge bases
- `get_contextual_suggestions(context)`: Get context-aware suggestions
- `find_similar(article_id)`: Find similar articles
- `get_article(article_id)`: Get specific article

### KnowledgeBase

- `add_article(article)`: Add an article
- `remove_article(article_id)`: Remove an article
- `update_article(article_id, updates)`: Update an article
- `load_from_markdown(path)`: Load from markdown files
- `export_to_json()`: Export knowledge base

## License

This project is published under [appropriate license].

## Related Packages

- `wish-models`: Core data models and validation
- `wish-core`: State management and event processing
- `wish-ai`: AI-driven inference engine
- `wish-tools`: Pentest tool integration
- `wish-c2`: C2 server integration
- `wish-cli`: Command line interface

## Support

If you have issues or questions, you can get support through:

- [Issues](../../issues): Bug reports and feature requests
- [Discussions](../../discussions): General questions and discussions
- Documentation: Knowledge base integration guides