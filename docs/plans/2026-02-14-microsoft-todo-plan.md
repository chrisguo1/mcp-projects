# Microsoft To Do MCP Server Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a read-only MCP server for Microsoft To Do using the Microsoft Graph API.

**Architecture:** Single-file FastMCP server with MSAL for OAuth2 device code flow and httpx for async Graph API calls. Formatting functions are pure and testable. Auth is handled via a helper that acquires tokens silently (from cache) or falls back to device code flow.

**Tech Stack:** Python 3.13, FastMCP, MSAL, httpx, pytest

---

### Task 1: Project Setup

**Files:**
- Modify: `pyproject.toml`
- Verify: `servers/microsoft_to_do/__init__.py` (already exists)

**Step 1: Add msal dependency**

Run: `uv add msal`

**Step 2: Update pyproject.toml pythonpath for tests**

In `pyproject.toml`, add `"servers/microsoft_to_do"` to the `pythonpath` list:

```toml
[tool.pytest.ini_options]
testpaths = ["servers"]
pythonpath = ["servers/apple_notes", "servers/weather", "servers/microsoft_to_do"]
```

**Step 3: Sync dependencies**

Run: `uv sync`

**Step 4: Commit**

```bash
git add pyproject.toml uv.lock
git commit -m "add msal dependency and pytest config for microsoft_to_do"
```

---

### Task 2: Format Task Lists — Test + Implementation

**Files:**
- Create: `servers/microsoft_to_do/test_microsoft_to_do.py`
- Create: `servers/microsoft_to_do/microsoft_to_do.py`

**Step 1: Write the failing test**

```python
"""Tests for Microsoft To Do MCP server formatting logic."""

import pytest

from microsoft_to_do import format_task_lists


class TestFormatTaskLists:
    def test_single_list(self):
        data = {
            "value": [
                {"id": "abc123", "displayName": "Tasks", "wellknownListName": "defaultList"}
            ]
        }
        result = format_task_lists(data)
        assert result == "- Tasks (id: abc123)"

    def test_multiple_lists(self):
        data = {
            "value": [
                {"id": "abc123", "displayName": "Tasks", "wellknownListName": "defaultList"},
                {"id": "def456", "displayName": "Shopping", "wellknownListName": "none"},
            ]
        }
        result = format_task_lists(data)
        assert "- Tasks (id: abc123)" in result
        assert "- Shopping (id: def456)" in result

    def test_empty_lists(self):
        data = {"value": []}
        result = format_task_lists(data)
        assert result == "No task lists found."
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest servers/microsoft_to_do/test_microsoft_to_do.py::TestFormatTaskLists -v`
Expected: FAIL (import error)

**Step 3: Write minimal implementation**

Create `servers/microsoft_to_do/microsoft_to_do.py` with:

```python
import logging

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("microsoft_to_do")

mcp = FastMCP("microsoft_to_do")


def format_task_lists(data: dict) -> str:
    lists = data.get("value", [])
    if not lists:
        return "No task lists found."
    return "\n".join(f"- {tl['displayName']} (id: {tl['id']})" for tl in lists)
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest servers/microsoft_to_do/test_microsoft_to_do.py::TestFormatTaskLists -v`
Expected: PASS

**Step 5: Commit**

```bash
git add servers/microsoft_to_do/microsoft_to_do.py servers/microsoft_to_do/test_microsoft_to_do.py
git commit -m "add format_task_lists with tests"
```

---

### Task 3: Format Tasks — Test + Implementation

**Files:**
- Modify: `servers/microsoft_to_do/test_microsoft_to_do.py`
- Modify: `servers/microsoft_to_do/microsoft_to_do.py`

**Step 1: Write the failing test**

Add to the test file:

```python
from microsoft_to_do import format_tasks


class TestFormatTasks:
    def _make_task(self, title="Buy groceries", task_id="task1", status="notStarted",
                   importance="normal", due_date=None):
        task = {
            "id": task_id,
            "title": title,
            "status": status,
            "importance": importance,
            "isReminderOn": False,
            "createdDateTime": "2026-01-15T10:00:00Z",
            "lastModifiedDateTime": "2026-01-15T12:00:00Z",
            "body": {"content": "", "contentType": "text"},
        }
        if due_date:
            task["dueDateTime"] = {"dateTime": due_date, "timeZone": "UTC"}
        return task

    def test_single_task(self):
        data = {"value": [self._make_task()]}
        result = format_tasks(data)
        assert "Buy groceries" in result
        assert "notStarted" in result

    def test_task_with_due_date(self):
        data = {"value": [self._make_task(due_date="2026-02-20T00:00:00.0000000")]}
        result = format_tasks(data)
        assert "2026-02-20" in result

    def test_task_with_high_importance(self):
        data = {"value": [self._make_task(importance="high")]}
        result = format_tasks(data)
        assert "high" in result

    def test_filters_completed_by_default(self):
        data = {"value": [
            self._make_task(title="Done task", status="completed"),
            self._make_task(title="Open task", status="notStarted"),
        ]}
        result = format_tasks(data)
        assert "Open task" in result
        assert "Done task" not in result

    def test_include_completed(self):
        data = {"value": [
            self._make_task(title="Done task", status="completed"),
            self._make_task(title="Open task", status="notStarted"),
        ]}
        result = format_tasks(data, include_completed=True)
        assert "Done task" in result
        assert "Open task" in result

    def test_empty_tasks(self):
        data = {"value": []}
        result = format_tasks(data)
        assert result == "No tasks found."

    def test_all_completed_filtered(self):
        data = {"value": [
            self._make_task(title="Done", status="completed"),
        ]}
        result = format_tasks(data)
        assert result == "No tasks found."
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest servers/microsoft_to_do/test_microsoft_to_do.py::TestFormatTasks -v`
Expected: FAIL (import error)

**Step 3: Write minimal implementation**

Add to `microsoft_to_do.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest servers/microsoft_to_do/test_microsoft_to_do.py::TestFormatTasks -v`
Expected: PASS

**Step 5: Commit**

```bash
git add servers/microsoft_to_do/microsoft_to_do.py servers/microsoft_to_do/test_microsoft_to_do.py
git commit -m "add format_tasks with filtering and tests"
```

---

### Task 4: Format Task Detail — Test + Implementation

**Files:**
- Modify: `servers/microsoft_to_do/test_microsoft_to_do.py`
- Modify: `servers/microsoft_to_do/microsoft_to_do.py`

**Step 1: Write the failing test**

Add to the test file:

```python
from microsoft_to_do import format_task_detail


class TestFormatTaskDetail:
    def _make_detail(self, title="Buy groceries", body_content="", checklist=None):
        return {
            "id": "task1",
            "title": title,
            "status": "notStarted",
            "importance": "high",
            "isReminderOn": True,
            "createdDateTime": "2026-01-15T10:00:00Z",
            "lastModifiedDateTime": "2026-01-15T12:00:00Z",
            "body": {"content": body_content, "contentType": "text"},
            "dueDateTime": {"dateTime": "2026-02-20T00:00:00.0000000", "timeZone": "UTC"},
            "categories": ["Important"],
            "_checklist_items": checklist or [],
        }

    def test_basic_detail(self):
        result = format_task_detail(self._make_detail())
        assert "Buy groceries" in result
        assert "high" in result
        assert "2026-02-20" in result

    def test_body_content_shown(self):
        result = format_task_detail(self._make_detail(body_content="Remember organic milk"))
        assert "Remember organic milk" in result

    def test_categories_shown(self):
        result = format_task_detail(self._make_detail())
        assert "Important" in result

    def test_checklist_items_shown(self):
        checklist = [
            {"displayName": "Milk", "isChecked": False},
            {"displayName": "Eggs", "isChecked": True},
        ]
        result = format_task_detail(self._make_detail(checklist=checklist))
        assert "[ ] Milk" in result
        assert "[x] Eggs" in result

    def test_empty_checklist(self):
        result = format_task_detail(self._make_detail(checklist=[]))
        assert "Checklist" not in result

    def test_no_due_date(self):
        detail = self._make_detail()
        del detail["dueDateTime"]
        result = format_task_detail(detail)
        assert "Buy groceries" in result
        assert "Due" not in result

    def test_reminder_shown(self):
        result = format_task_detail(self._make_detail())
        assert "Reminder: on" in result
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest servers/microsoft_to_do/test_microsoft_to_do.py::TestFormatTaskDetail -v`
Expected: FAIL (import error)

**Step 3: Write minimal implementation**

Add to `microsoft_to_do.py`:

```python
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
```

**Step 4: Run test to verify it passes**

Run: `uv run pytest servers/microsoft_to_do/test_microsoft_to_do.py::TestFormatTaskDetail -v`
Expected: PASS

**Step 5: Commit**

```bash
git add servers/microsoft_to_do/microsoft_to_do.py servers/microsoft_to_do/test_microsoft_to_do.py
git commit -m "add format_task_detail with checklist support and tests"
```

---

### Task 5: Auth Layer — MSAL Device Code Flow

**Files:**
- Modify: `servers/microsoft_to_do/microsoft_to_do.py`

**Step 1: Implement the auth helper**

Add to `microsoft_to_do.py`, after the logger setup and before the format functions:

```python
import json
import os
import sys
from pathlib import Path

import msal

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
```

**Step 2: Verify it parses correctly**

Run: `python -c "import ast; ast.parse(open('servers/microsoft_to_do/microsoft_to_do.py').read()); print('OK')"`
Expected: OK

**Step 3: Commit**

```bash
git add servers/microsoft_to_do/microsoft_to_do.py
git commit -m "add MSAL auth layer with device code flow and token caching"
```

---

### Task 6: API Layer + MCP Tools

**Files:**
- Modify: `servers/microsoft_to_do/microsoft_to_do.py`

**Step 1: Add the Graph API helper and MCP tools**

Add the httpx import at the top, then add after the auth functions:

```python
import httpx


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
        # Fetch checklist items separately
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
```

**Step 2: Run all tests to verify nothing broke**

Run: `uv run pytest servers/microsoft_to_do/ -v`
Expected: All tests PASS

**Step 3: Verify the module loads without env vars (should fail fast)**

Run: `uv run python -c "from microsoft_to_do import mcp; print('Module loads OK')"`
Expected: Prints "Module loads OK" (the env var check happens at token acquisition time, not import time)

**Step 4: Commit**

```bash
git add servers/microsoft_to_do/microsoft_to_do.py
git commit -m "add Graph API layer and MCP tool definitions"
```

---

### Task 7: Final Verification and Cleanup

**Files:**
- Modify: `.gitignore`
- Verify all files

**Step 1: Add token cache to .gitignore**

Ensure `.mcp-microsoft-todo-cache.json` won't accidentally be committed. Add to `.gitignore`:

```
.mcp-microsoft-todo-cache.json
```

**Step 2: Run the full test suite**

Run: `uv run pytest servers/ -v`
Expected: All tests across all servers PASS

**Step 3: Verify the server can at least start up (will fail on auth but proves wiring)**

Run: `echo '{}' | MICROSOFT_TODO_CLIENT_ID=test timeout 3 uv run python servers/microsoft_to_do/microsoft_to_do.py 2>&1 || true`
Expected: Server starts (you'll see log output), then times out or errors on stdin close — this proves the FastMCP wiring works

**Step 4: Commit**

```bash
git add .gitignore
git commit -m "add token cache to gitignore"
```

---

### Summary

| Task | What | Tests |
|------|------|-------|
| 1 | Project setup (deps, pytest config) | — |
| 2 | `format_task_lists` | 3 tests |
| 3 | `format_tasks` | 7 tests |
| 4 | `format_task_detail` | 7 tests |
| 5 | Auth layer (MSAL device code) | — |
| 6 | API layer + MCP tools | verify existing pass |
| 7 | Final verification + cleanup | full suite |

Total: 17 unit tests for formatting logic. Auth and API layers are integration-tested manually (require real Microsoft account).
