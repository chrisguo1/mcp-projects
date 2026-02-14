---
name: add-mcp-locally
description: Adds MCPs in this project locally to apps like Claude for Desktop.
---

# Add MCP Servers Locally

This skill registers MCP servers from this project into local apps so they can be used.

## Steps

1. **Discover servers**: Scan the `servers/` directory in this project. Each subdirectory containing a `.py` file with a `FastMCP` instance is an MCP server.

2. **Resolve `uv` path**: Run `which uv` to get the absolute path to the `uv` binary. GUI apps like Claude Desktop don't inherit shell PATH, so the full path is required.

3. **Register in Claude for Desktop**:
   - Config file location: `~/Library/Application Support/Claude/claude_desktop_config.json`
   - Read the existing config (create if missing)
   - For each discovered server, add/update an entry under `mcpServers` with this format:
     ```json
     {
       "<server-name>": {
         "command": "<absolute-path-to-uv>",
         "args": [
           "--directory",
           "<absolute-path-to-server-subdirectory>",
           "run",
           "<server-filename>.py"
         ]
       }
     }
     ```
   - `<server-name>` is the subdirectory name (e.g. `weather`)
   - `<absolute-path-to-server-subdirectory>` is the full path to that server's directory (e.g. `/Users/.../servers/weather`)
   - Preserve any existing config entries and preferences

4. **Report results**: List which servers were added/updated and remind the user to restart Claude Desktop.
