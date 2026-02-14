"""Tests for Microsoft To Do MCP server formatting logic."""

import pytest

from microsoft_to_do import format_task_lists, format_tasks


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
