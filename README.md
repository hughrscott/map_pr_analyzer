# MCP PR Template Analyzer

An MCP (Model Context Protocol) server that helps analyze pull requests and suggest appropriate PR templates based on code changes.

## What This Does

This MCP server provides Claude with tools to:
1. **Analyze git changes** - Get detailed diff data, file changes, and statistics
2. **Manage PR templates** - Access and organize different PR templates
3. **Suggest templates** - Recommend appropriate templates based on actual code changes

## Philosophy

Instead of building complex rule-based logic, this server provides Claude with rich, raw data and lets Claude's intelligence make the decisions. This approach is more flexible and accurate than traditional rule-based systems.

## Installation

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone/create the project
uv init mcp-pr-analyzer
cd mcp-pr-analyzer

# Install dependencies
uv add fastmcp GitPython
```

## Usage

### Running the Server

```bash
# Development mode
uv run src/server.py

# Or with specific options
uv run python src/server.py
```

### Available Tools

1. **`analyze_file_changes`**
   - Analyzes git diff between branches
   - Returns file changes, diff content, and statistics
   -