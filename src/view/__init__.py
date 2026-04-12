"""
View layer (view).
Handles user interaction: CLI argument parsing and terminal rendering.
"""

from .cli import (
  parse_arguments,
  show_welcome,
  show_no_repos_found,
  show_start_processing,
  show_result,
  show_auth_fallback,
  show_auth_fallback_start,
  show_clean_warning,
  show_summary,
  prompt_for_credentials,
  show_auth_success,
  show_branches_compact,
  show_ci_compact,
  show_groups_summary,
  show_sync_preview,
  show_interactive_prompt,
  show_git_diff,
  console
)

__all__ = [
  "parse_arguments",
  "show_welcome",
  "show_no_repos_found",
  "show_start_processing",
  "show_result",
  "show_auth_fallback",
  "show_auth_fallback_start",
  "show_clean_warning",
  "show_summary",
  "prompt_for_credentials",
  "show_auth_success",
  "show_branches_compact",
  "show_ci_compact",
  "show_groups_summary",
  "show_sync_preview",
  "show_interactive_prompt",
  "show_git_diff",
  "console"
]