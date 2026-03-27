"""
tests/test_error_handler.py

Test suite for src/model/error_handler.py.
Verifies that GitPython errors are correctly translated
into user-friendly English messages for terminal display.
"""

import os
import sys
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from model.error_handler import parse_git_error


def _make_git_error(stderr_text: str):
    """Builds a mock exc.GitCommandError with the given stderr content."""
    from git import exc
    error = MagicMock(spec=exc.GitCommandError)
    # Empty or None stderr activates the str(e) fallback in parse_git_error
    error.stderr = stderr_text if stderr_text else None
    return error


class TestParseGitError(unittest.TestCase):

    def test_network_error_unresolved_host(self):
        err = _make_git_error("fatal: Could not resolve host: github.com")
        result = parse_git_error(err)
        self.assertIn("Network error", result)

    def test_authentication_error(self):
        err = _make_git_error("remote: Permission denied to user.")
        result = parse_git_error(err)
        self.assertIn("Authentication error", result)

    def test_divergent_branches_error(self):
        err = _make_git_error("hint: Not possible to fast-forward, aborting.")
        result = parse_git_error(err)
        self.assertIn("Divergent branches", result)

    def test_directory_already_exists_error(self):
        err = _make_git_error("fatal: destination path 'repo' already exists and is not an empty directory.")
        result = parse_git_error(err)
        self.assertIn("System conflict", result)

    def test_unknown_error_is_truncated(self):
        # Generate stderr with more than 3 lines to trigger the truncation branch
        stderr = "\n".join([f"line {i}" for i in range(10)])
        err = _make_git_error(stderr)
        result = parse_git_error(err)
        self.assertIn("truncated", result.lower())

    def test_empty_stderr_returns_non_empty_string(self):
        """
        When stderr is None, parse_git_error must not raise and must
        always return a non-empty string as a fallback.
        """
        from git import exc
        error = exc.GitCommandError("git fetch", 128)
        error.stderr = None
        result = parse_git_error(error)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)


if __name__ == "__main__":
    unittest.main()
