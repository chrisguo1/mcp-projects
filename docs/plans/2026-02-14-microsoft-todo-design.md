# Microsoft To Do MCP Server — Design

## Summary

Read-only MCP server for Microsoft To Do, built with FastMCP (Python). Uses MSAL for OAuth2 device code flow authentication and httpx for async Microsoft Graph API calls.

## Architecture

Single-file FastMCP server (`servers/microsoft_to_do/microsoft_to_do.py`) with two layers:

1. **Auth layer** — MSAL `PublicClientApplication` with device code flow. Token cache serialized to `~/.mcp-microsoft-todo-cache.json`. Attempts silent token acquisition on each call; falls back to device code flow if no valid cached token.

2. **API layer** — Async `httpx.AsyncClient` calling Microsoft Graph API v1.0 (`https://graph.microsoft.com/v1.0/me/todo/...`).

### Configuration

Environment variables:
- `MICROSOFT_TODO_CLIENT_ID` (required) — Azure AD app registration client ID
- `MICROSOFT_TODO_TENANT_ID` (optional, defaults to `"consumers"` for personal Microsoft accounts)

### Graph API Permission

- `Tasks.Read` — minimum scope for read-only access

## Tools

### `get_task_lists()`
- Lists all task lists (name + ID)
- Endpoint: `GET /me/todo/lists`

### `get_tasks(list_id: str, include_completed: bool = False)`
- Lists tasks from a specific list
- Filters out completed tasks by default
- Shows: title, due date, importance, status
- Endpoint: `GET /me/todo/lists/{list_id}/tasks`

### `get_task_detail(list_id: str, task_id: str)`
- Full detail for a single task
- Includes: body content, recurrence, reminders, checklist items (subtasks)
- Endpoint: `GET /me/todo/lists/{list_id}/tasks/{task_id}`

## Error Handling

- **Auth failures** — Clear message asking user to re-authenticate
- **API errors (4xx/5xx)** — User-friendly error with status code
- **Network timeouts** — 30-second timeout
- **Missing env vars** — Fail fast at startup with clear message

## Logging

- Logger name: `"microsoft_to_do"`
- Level: INFO
- Logs: startup/shutdown, auth events (device code initiated, token acquired/refreshed, failures), API endpoints called, exceptions
- Does NOT log: task titles, content, list names, or any personal data
- Output: stderr (standard for stdio transport MCP servers)

## Testing

- Unit tests for response parsing and formatting
- Mocked Graph API responses (no live API calls)
- Generic placeholder data only (per CLAUDE.md rules)

## Dependencies

- `msal` — OAuth2 device code flow + token caching
- `httpx` — async HTTP client (already in project)
- `mcp[cli]` — FastMCP framework (already in project)

## Decisions

- **MSAL over raw OAuth2**: Handles token lifecycle (caching, refresh, retry) correctly out of the box
- **Device code flow over client credentials**: Interactive flow appropriate for personal MCP usage
- **User-registered Azure AD app**: No shared credentials, user controls their own app registration
- **Read-only scope**: Safest starting point; write operations can be added later
- **Single file**: Matches existing server conventions (Apple Notes, Weather)
