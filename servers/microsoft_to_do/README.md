# Microsoft To Do MCP Server

A read-only MCP server for Microsoft To Do. Lets Claude read your task lists, tasks, and task details via the Microsoft Graph API.

## Prerequisites

- Python 3.13+
- [uv](https://docs.astral.sh/uv/) package manager
- A Microsoft account with To Do tasks

## Azure App Registration

You need to register an app in Azure AD to get a client ID:

1. Go to [Azure App Registrations](https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps)
2. Click **New registration**
3. Set a name (e.g. "MCP Microsoft To Do")
4. Under **Supported account types**, select **Personal Microsoft accounts only** (or include work/school if needed)
5. Under **Redirect URI**, select **Public client/native** and set the URI to `https://login.microsoftonline.com/common/oauth2/nativeclient`
6. Click **Register**
7. Copy the **Application (client) ID** — this is your `MICROSOFT_TODO_CLIENT_ID`
8. Go to **API permissions** > **Add a permission** > **Microsoft Graph** > **Delegated permissions**
9. Search for and add **Tasks.Read**
10. Click **Grant admin consent** (or consent will be requested on first login)

## Configuration

| Environment Variable       | Required | Default     | Description                                                                                                                 |
| -------------------------- | -------- | ----------- | --------------------------------------------------------------------------------------------------------------------------- |
| `MICROSOFT_TODO_CLIENT_ID` | Yes      | —           | Azure AD app registration client ID                                                                                         |
| `MICROSOFT_TODO_TENANT_ID` | No       | `consumers` | Azure AD tenant. Use `consumers` for personal Microsoft accounts, `organizations` for work/school, or a specific tenant ID. |

## Running the Server

```bash
MICROSOFT_TODO_CLIENT_ID=your-client-id uv run python servers/microsoft_to_do/microsoft_to_do.py
```

### Claude for Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "microsoft_to_do": {
      "command": "/path/to/uv",
      "args": ["run", "python", "servers/microsoft_to_do/microsoft_to_do.py"],
      "cwd": "/path/to/mcp-projects",
      "env": {
        "MICROSOFT_TODO_CLIENT_ID": "your-client-id"
      }
    }
  }
}
```

### Claude Code

Add to `.claude/settings.local.json` or run with the env var set.

## Authentication

On first use, the server starts a **device code flow**:

1. A message appears in stderr with a URL and a code
2. Open the URL in your browser
3. Enter the code and sign in with your Microsoft account
4. Grant the requested permissions

After authentication, the token is cached at `~/.mcp-microsoft-todo-cache.json` and refreshed automatically. You only need to authenticate once unless the token expires and can't be refreshed.

To re-authenticate, delete the cache file:

```bash
rm ~/.mcp-microsoft-todo-cache.json
```

## Tools

### `get_task_lists()`

Lists all your To Do task lists with names and IDs.

Example output:
```
- Tasks (id: AAMkADIyAAAAABrJAAA=)
- Shopping (id: AAMkADIyAAAEFTTrJAAA=)
```

### `get_tasks(list_id, include_completed=False)`

Lists tasks from a specific list. Filters out completed tasks by default.

| Parameter           | Type | Description                              |
| ------------------- | ---- | ---------------------------------------- |
| `list_id`           | str  | Task list ID (from `get_task_lists`)     |
| `include_completed` | bool | Include completed tasks (default: False) |

Example output:
```
- Buy groceries [notStarted, due: 2026-02-20, importance: high] (id: 721a35e2)
- Call dentist [notStarted] (id: 8a3b1c4d)
```

### `get_task_detail(list_id, task_id)`

Full details for a single task, including body text and checklist items.

| Parameter | Type | Description                |
| --------- | ---- | -------------------------- |
| `list_id` | str  | Task list ID               |
| `task_id` | str  | Task ID (from `get_tasks`) |

Example output:
```
# Buy groceries
Status: notStarted
Importance: high
Due: 2026-02-20
Reminder: on
Categories: Important
Created: 2026-01-15T10:00:00Z
Modified: 2026-01-15T12:00:00Z

Checklist:
  [ ] Milk
  [x] Eggs
  [ ] Bread
```

## Running Tests

```bash
uv run pytest servers/microsoft_to_do/ -v
```
