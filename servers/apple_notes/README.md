# Apple Notes MCP Server

An MCP server that provides read-only access to Apple Notes on macOS.

## Tools

| Tool | Description |
|------|-------------|
| `get_folders` | List all folders in Apple Notes. |
| `get_notes` | List notes with title, folder, modification date, and lock status. Accepts an optional `folder` parameter to filter. |
| `get_note_content` | Read a note's full content as markdown, given its exact title. |

## Design Decisions

**AppleScript via `osascript`, not direct SQLite access.**
The Apple Notes SQLite database (`NoteStore.sqlite`) requires Full Disk Access -- a broad macOS permission that grants access to Mail, Messages, Safari data, and more. AppleScript requires only the Automation permission, which is scoped specifically to the Notes app.

**HTML converted to markdown, not plain text.**
Apple Notes stores note bodies as HTML. Stripping to plain text destroys semantic structure: headings, lists, and formatting collapse into an undifferentiated blob. Converting to markdown (via `markdownify`) preserves that structure while remaining token-efficient for LLM consumption.

**Password-protected notes.**
Titles of locked notes are visible in `get_notes` listings (with a `(locked)` suffix), matching the behavior of the Notes app itself. `get_note_content` will not return the body of a locked note.

**Orphaned and deleted notes.**
Notes that lack valid folder metadata (e.g., recently-deleted notes) are silently skipped in listings rather than causing errors.

**`asyncio.to_thread` for subprocess calls.**
AppleScript runs via `subprocess.run`, which is blocking. The MCP server is async (FastMCP tools are `async def`), so calling `subprocess.run` directly would block the event loop while waiting for `osascript` to finish (up to 30 seconds). `asyncio.to_thread` runs the blocking call on a separate thread, keeping the event loop free to handle other requests.

## Requirements

- macOS (uses `osascript`)
- Python >= 3.13
- Dependencies: `mcp[cli]`, `markdownify`

When the server is first invoked, macOS will prompt to grant Automation permission for the host app to control Notes.
