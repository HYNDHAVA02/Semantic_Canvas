Implement $ARGUMENTS following the plan we agreed on.

Work in this order:
1. **Database migration** (if needed) — new file in `packages/api/src/db/migrations/`
2. **Repository method** — add to appropriate repository in `packages/api/src/repositories/`
3. **Service class** (if shared logic) — add to `packages/api/src/services/`
4. **MCP tool** (if needed) — create in `packages/api/src/mcp/tools/`, register in registry
5. **REST endpoint** (if needed) — add controller method + DTO
6. **Tests** — write tests for repository, then MCP tool, then REST endpoint

After each step, run the relevant checks:
- After Python changes: `ruff check . && mypy src/`
- After test changes: `pytest <test_file>`
- After everything: `pytest`

Show me what you've done after each step before moving to the next.
Do NOT skip tests. Every repository method and MCP tool gets a test.
