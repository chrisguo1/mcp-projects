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
