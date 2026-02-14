# MCP Projects

Some MCP servers/clients I built.

## Servers

- **Weather** — Get weather forecasts and alerts for US locations via the National Weather Service API.
- **Apple Notes** — Access and list Apple Notes from your local machine.

## Local Development

### Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/)

### Installing Environment

```bash
uv sync
```

### Running Locally

```bash
uv --directory servers/<server_name> run <server_name>.py
```

For example:

```bash
uv --directory servers/weather run weather.py
uv --directory servers/apple_notes run apple_notes.py
```

### Adding to Claude for Desktop

Add an entry to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "<server_name>": {
      "command": "/full/path/to/uv",
      "args": [
        "--directory",
        "/full/path/to/mcp-projects/servers/<server_name>",
        "run",
        "<server_name>.py"
      ]
    }
  }
}
```

Use the full path to `uv` (find it with `which uv`) since GUI apps don't inherit your shell PATH.