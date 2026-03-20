Add a new MCP tool called $ARGUMENTS.

Follow this checklist:

1. **Define the tool** in `packages/api/src/mcp/tools/<tool_name>.py`:
   - Pydantic model for parameters
   - Handler function: validate → call repository → return result
   - Tool metadata: name, description (clear enough for an AI agent to know when to use it)

2. **Add repository method** in the appropriate repository file:
   - Parameterized SQL query
   - Typed return value

3. **Register** in `packages/api/src/mcp/registry.py`

4. **Write tests** in `packages/api/tests/test_mcp_tools/test_<tool_name>.py`:
   - Valid input → expected output
   - Missing required params → validation error
   - Empty results → empty list (not error)

5. **Run checks**:
   ```
   ruff check packages/api/ && mypy packages/api/src/
   cd packages/api && pytest tests/test_mcp_tools/test_<tool_name>.py
   ```

Reference existing tools in `packages/api/src/mcp/tools/` for the pattern.
