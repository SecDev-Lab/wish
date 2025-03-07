# wish-log-analysis

Log analysis package for wish.

## Development

### Graph Visualization

The log analysis graph can be visualized using the following command:

```bash
# グラフを可視化してdocs/graph.svgとdocs/design.mdを更新
uv sync --dev
uv run python scripts/update_graph_visualization.py
```

This will generate an SVG visualization of the graph and update the `docs/design.md` file.

## Environment Setup

To use this package, you need to set up the following environment variables:

1. Create a `.env` file (you can copy `.env.example` as a starting point)
2. Configure the required environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `OPENAI_MODEL`: The OpenAI model to use (default: gpt-4o)

Example:

```bash
# .env file
OPENAI_API_KEY=your-api-key-here
OPENAI_MODEL=gpt-4o
```

## Future work

- English Prompt
- API client/server
