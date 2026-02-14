"""Tests for Apple Notes MCP server parsing logic."""

import pytest

from apple_notes import (
    DELIM,
    _html_to_markdown,
    _parse_folders,
    _parse_note_content,
    _parse_notes,
)


class TestParseFolders:
    def test_single_folder(self):
        assert _parse_folders("Notes") == "- Notes"

    def test_multiple_folders(self):
        result = _parse_folders("Archive, Notes, Work")
        assert result == "- Archive\n- Notes\n- Work"

    def test_empty_returns_not_found(self):
        assert _parse_folders("") == "No folders found."


class TestParseNotes:
    def _make_line(self, title, folder, date, locked=False):
        line = f"{title}{DELIM}{folder}{DELIM}{date}"
        if locked:
            line += f"{DELIM}locked"
        return line

    def test_single_note(self):
        raw = self._make_line("My Note", "Notes", "Jan 1, 2026")
        result = _parse_notes(raw)
        assert result == "- My Note  [folder: Notes, modified: Jan 1, 2026]"

    def test_multiple_notes(self):
        raw = "\n".join(
            [
                self._make_line("Note A", "Notes", "Jan 1, 2026"),
                self._make_line("Note B", "Work", "Feb 2, 2026"),
            ]
        )
        result = _parse_notes(raw)
        assert "- Note A  [folder: Notes" in result
        assert "- Note B  [folder: Work" in result

    def test_locked_note_tagged(self):
        raw = self._make_line("Secret", "Notes", "Jan 1, 2026", locked=True)
        result = _parse_notes(raw)
        assert "(locked)" in result

    def test_unlocked_note_not_tagged(self):
        raw = self._make_line("Public", "Notes", "Jan 1, 2026", locked=False)
        result = _parse_notes(raw)
        assert "(locked)" not in result

    def test_empty_returns_not_found(self):
        assert _parse_notes("") == "No notes found."

    def test_malformed_line_skipped(self):
        raw = "just some garbage without delimiters"
        assert _parse_notes(raw) == "No notes found."

    def test_mixed_locked_and_unlocked(self):
        raw = "\n".join(
            [
                self._make_line("Public", "Notes", "Jan 1, 2026"),
                self._make_line("Private", "Notes", "Jan 2, 2026", locked=True),
            ]
        )
        result = _parse_notes(raw)
        lines = result.split("\n")
        assert "(locked)" not in lines[0]
        assert "(locked)" in lines[1]


class TestParseNoteContent:
    def test_not_found_sentinel(self):
        result = _parse_note_content("NOT_FOUND", "My Note")
        assert result == 'Note "My Note" not found or is password-protected.'

    def test_html_converted_to_markdown(self):
        result = _parse_note_content("<div><h1>Title</h1></div>", "Title")
        assert "# Title" in result

    def test_blank_lines_collapsed(self):
        html = "<div>one</div>" + "<div><br></div>" * 5 + "<div>two</div>"
        result = _parse_note_content(html, "Test")
        assert "\n\n\n" not in result
        assert "one" in result
        assert "two" in result
