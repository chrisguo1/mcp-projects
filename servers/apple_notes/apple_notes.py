import asyncio
import logging
import re
import subprocess

from markdownify import markdownify
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("apple_notes")

mcp = FastMCP("apple_notes")


def _html_to_markdown(html: str) -> str:
    md = markdownify(html, heading_style="ATX", bullets="-")
    # Collapse runs of 3+ blank lines down to 2
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip()


def _run_applescript(script: str) -> str:
    result = subprocess.run(
        ["osascript", "-e", script],
        capture_output=True,
        text=True,
        timeout=30,
    )
    if result.returncode != 0:
        logger.error("AppleScript failed: %s", result.stderr.strip())
        raise RuntimeError(f"AppleScript error: {result.stderr.strip()}")
    return result.stdout.strip()


DELIM = "|||"


def _parse_folders(raw: str) -> str:
    if not raw:
        return "No folders found."
    folders = [f.strip() for f in raw.split(", ")]
    return "\n".join(f"- {f}" for f in folders)


def _parse_notes(raw: str) -> str:
    if not raw:
        return "No notes found."
    lines = []
    for line in raw.strip().split("\n"):
        parts = line.split(DELIM)
        if len(parts) >= 3:
            title, note_folder, modified = parts[0], parts[1], parts[2]
            locked = len(parts) >= 4 and parts[3] == "locked"
            suffix = " (locked)" if locked else ""
            lines.append(
                f"- {title}  [folder: {note_folder}, modified: {modified}]{suffix}"
            )
    return "\n".join(lines) if lines else "No notes found."


def _parse_note_content(raw: str, title: str) -> str:
    if raw == "NOT_FOUND":
        return f'Note "{title}" not found or is password-protected.'
    return _html_to_markdown(raw)


@mcp.tool()
async def get_folders() -> str:
    """Get a list of all folders in Apple Notes."""
    logger.info("Listing folders")
    script = 'tell application "Notes" to get name of every folder'
    raw = await asyncio.to_thread(_run_applescript, script)
    return _parse_folders(raw)


@mcp.tool()
async def get_notes(folder: str | None = None) -> str:
    """Get a list of notes with titles, folder, and modification dates.

    Args:
        folder: Optional folder name to filter by. Lists all notes if not provided.
    """
    if folder:
        escaped_folder = folder.replace('"', '\\"')
        folder_loop = f'set folderList to {{folder "{escaped_folder}"}}'
    else:
        folder_loop = "set folderList to every folder"

    script = f"""
tell application "Notes"
    set output to ""
    set d to "{DELIM}"
    {folder_loop}
    repeat with f in folderList
        repeat with n in every note of f
            set isLocked to password protected of n
            if isLocked then
                set lockTag to d & "locked"
            else
                set lockTag to ""
            end if
            set output to output & name of n & d & name of f & d & (modification date of n as string) & lockTag & linefeed
        end repeat
    end repeat
    return output
end tell
"""
    logger.info("Listing notes%s", f" in folder '{folder}'" if folder else "")
    raw = await asyncio.to_thread(_run_applescript, script)
    return _parse_notes(raw)


@mcp.tool()
async def get_note_content(title: str) -> str:
    """Read the full content of a specific note by its title.
    Returns plain text with HTML stripped. Refuses to read password-protected notes.

    Args:
        title: The exact title of the note to read.
    """
    escaped_title = title.replace('"', '\\"')
    script = f"""
tell application "Notes"
    set matchedNotes to every note whose name is "{escaped_title}" and password protected is false
    if (count of matchedNotes) is 0 then
        return "NOT_FOUND"
    end if
    set n to item 1 of matchedNotes
    return body of n
end tell
"""
    logger.info("Reading note: %s", title)
    raw = await asyncio.to_thread(_run_applescript, script)
    return _parse_note_content(raw, title)


def main():
    logger.info("Starting Apple Notes MCP server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
