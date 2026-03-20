Review the current branch for PR readiness.

1. Run `git diff main --stat` to see what changed
2. For each changed file, check:
   - Does it follow the conventions in CLAUDE.md?
   - Are there type hints on all function signatures?
   - Are Pydantic models used for external input validation?
   - Is SQL parameterized (no string interpolation)?
   - Does every new public function have a docstring?
3. Run `ruff check . && mypy packages/api/src/ && pytest` and report results
4. Check: are there tests for every new repository method and MCP tool?
5. Check: if there's a new migration, does it have a corresponding rollback?
6. Suggest a PR title and description following conventional commits

Be critical. Flag anything that would fail code review.
