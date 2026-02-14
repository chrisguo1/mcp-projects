import logging
import os
import sys
from pathlib import Path

import httpx
import msal
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("microsoft_to_do")

mcp = FastMCP("microsoft_to_do")

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
SCOPES = ["Tasks.Read"]
TOKEN_CACHE_PATH = Path.home() / ".mcp-microsoft-todo-cache.json"


def _build_msal_app() -> msal.PublicClientApplication:
    client_id = os.environ.get("MICROSOFT_TODO_CLIENT_ID")
    if not client_id:
        raise RuntimeError(
            "MICROSOFT_TODO_CLIENT_ID environment variable is required. "
            "Register an app at https://portal.azure.com/#blade/Microsoft_AAD_RegisteredApps"
        )
    tenant_id = os.environ.get("MICROSOFT_TODO_TENANT_ID", "consumers")

    cache = msal.SerializableTokenCache()
    if TOKEN_CACHE_PATH.exists():
        cache.deserialize(TOKEN_CACHE_PATH.read_text())

    app = msal.PublicClientApplication(
        client_id,
        authority=f"https://login.microsoftonline.com/{tenant_id}",
        token_cache=cache,
    )
    return app


def _save_token_cache(app: msal.PublicClientApplication) -> None:
    if app.token_cache.has_state_changed:
        TOKEN_CACHE_PATH.write_text(app.token_cache.serialize())


def _acquire_token(app: msal.PublicClientApplication) -> str:
    accounts = app.get_accounts()
    if accounts:
        result = app.acquire_token_silent(SCOPES, account=accounts[0])
        if result and "access_token" in result:
            logger.info("Token acquired from cache")
            _save_token_cache(app)
            return result["access_token"]

    logger.info("No cached token, starting device code flow")
    flow = app.initiate_device_flow(scopes=SCOPES)
    if "user_code" not in flow:
        raise RuntimeError(f"Device code flow failed: {flow.get('error_description', 'Unknown error')}")

    # Print to stderr so it shows in MCP server logs, not stdout (which is the MCP transport)
    print(f"\n{flow['message']}\n", file=sys.stderr, flush=True)

    result = app.acquire_token_by_device_flow(flow)
    if "access_token" not in result:
        raise RuntimeError(f"Authentication failed: {result.get('error_description', 'Unknown error')}")

    logger.info("Token acquired via device code flow")
    _save_token_cache(app)
    return result["access_token"]


async def _graph_get(path: str) -> dict:
    app = _build_msal_app()
    token = _acquire_token(app)
    url = f"{GRAPH_BASE}{path}"
    logger.info("GET %s", path)
    async with httpx.AsyncClient() as client:
        response = await client.get(
            url,
            headers={"Authorization": f"Bearer {token}"},
            timeout=30.0,
        )
        response.raise_for_status()
        return response.json()


def format_task_lists(data: dict) -> str:
    lists = data.get("value", [])
    if not lists:
        return "No task lists found."
    return "\n".join(f"- {tl['displayName']} (id: {tl['id']})" for tl in lists)


def format_tasks(data: dict, include_completed: bool = False) -> str:
    tasks = data.get("value", [])
    if not include_completed:
        tasks = [t for t in tasks if t.get("status") != "completed"]
    if not tasks:
        return "No tasks found."
    lines = []
    for t in tasks:
        due = ""
        if dt := t.get("dueDateTime"):
            due = f", due: {dt['dateTime'][:10]}"
        importance = t.get("importance", "normal")
        imp = f", importance: {importance}" if importance != "normal" else ""
        lines.append(f"- {t['title']} [{t['status']}{due}{imp}] (id: {t['id']})")
    return "\n".join(lines)


def format_task_detail(task: dict) -> str:
    lines = [f"# {task['title']}"]
    lines.append(f"Status: {task['status']}")
    lines.append(f"Importance: {task['importance']}")
    if dt := task.get("dueDateTime"):
        lines.append(f"Due: {dt['dateTime'][:10]}")
    lines.append(f"Reminder: {'on' if task.get('isReminderOn') else 'off'}")
    if cats := task.get("categories"):
        lines.append(f"Categories: {', '.join(cats)}")
    lines.append(f"Created: {task['createdDateTime']}")
    lines.append(f"Modified: {task['lastModifiedDateTime']}")
    if body := task.get("body", {}).get("content"):
        lines.append(f"\n{body}")
    checklist = task.get("_checklist_items", [])
    if checklist:
        lines.append("\nChecklist:")
        for item in checklist:
            check = "x" if item.get("isChecked") else " "
            lines.append(f"  [{check}] {item['displayName']}")
    return "\n".join(lines)


@mcp.tool()
async def get_task_lists() -> str:
    """Get all Microsoft To Do task lists with their names and IDs."""
    try:
        data = await _graph_get("/me/todo/lists")
        return format_task_lists(data)
    except Exception as e:
        logger.error("Failed to get task lists: %s", e)
        return f"Error fetching task lists: {e}"


@mcp.tool()
async def get_tasks(list_id: str, include_completed: bool = False) -> str:
    """Get tasks from a specific Microsoft To Do task list.

    Args:
        list_id: The ID of the task list (get IDs from get_task_lists).
        include_completed: Whether to include completed tasks. Defaults to False.
    """
    try:
        data = await _graph_get(f"/me/todo/lists/{list_id}/tasks")
        return format_tasks(data, include_completed=include_completed)
    except Exception as e:
        logger.error("Failed to get tasks: %s", e)
        return f"Error fetching tasks: {e}"


@mcp.tool()
async def get_task_detail(list_id: str, task_id: str) -> str:
    """Get full details for a specific Microsoft To Do task, including body and checklist items.

    Args:
        list_id: The ID of the task list.
        task_id: The ID of the task.
    """
    try:
        task = await _graph_get(f"/me/todo/lists/{list_id}/tasks/{task_id}")
        try:
            checklist_data = await _graph_get(
                f"/me/todo/lists/{list_id}/tasks/{task_id}/checklistItems"
            )
            task["_checklist_items"] = checklist_data.get("value", [])
        except Exception:
            task["_checklist_items"] = []
        return format_task_detail(task)
    except Exception as e:
        logger.error("Failed to get task detail: %s", e)
        return f"Error fetching task detail: {e}"


def main():
    logger.info("Starting Microsoft To Do MCP server")
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
