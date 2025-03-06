# wish-command-generation

Command generation package for wish.

## Development

### Graph Visualization

The command generation graph can be visualized using the following command:

```bash
# グラフを可視化してdocs/graph.svgとdocs/design.mdを更新
uv sync --dev
uv run python scripts/update_graph_visualization.py
```

This will generate an SVG visualization of the graph and update the `docs/design.md` file.

## Future work

- Robust command generation (NETWORK_ERROR, TIMEOUT handling in Dify implementation)
- Modify each command, as in Dify implementation
