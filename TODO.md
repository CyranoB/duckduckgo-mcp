# Features to Implement

## High Priority (Completed)

### 1. LLM-Friendly Output Format Option
- [x] Add `output_format` parameter to `duckduckgo_search` tool
  - `"json"` (default) - current behavior, returns list of dicts
  - `"text"` - natural language formatted output for LLMs
- [x] Include position numbering in results
- [x] Format as numbered list with title, URL, and summary
- [x] Add helpful "no results" message with suggestions

### 2. Dockerfile
- [x] Create `Dockerfile` for containerized deployment
- [x] Use Python 3.12-slim base image
- [x] Ensure proper entrypoint for MCP server mode
- [x] Add to `.dockerignore` for clean builds

### 3. Smithery Configuration
- [x] Create `smithery.yaml` for MCP ecosystem discoverability
- [x] Enable one-click installation via `npx @smithery/cli install`
- [x] Add Smithery badge to README.md

## Medium Priority

### 4. Explicit Rate Limiting
- [ ] Add configurable `RateLimiter` class
- [ ] Apply rate limiting to Jina fetch (external API dependency)
- [ ] Log when rate limiting is active
- [ ] Make limits configurable (default: 30 req/min search, 20 req/min fetch)

### 5. Better Error Messaging
- [x] Improve "no results" message with actionable suggestions (done in text format)
- [ ] Add context about potential causes (rate limiting, query issues)
- [ ] Include truncation details (original vs truncated length)

### 6. Position Numbering in Results
- [x] Position numbering included in text output format
- [ ] Add `position` field to JSON result dictionaries (optional)

## Low Priority (Nice to Have)

### 7. Enhanced Truncation Feedback
- [ ] Show original content length when truncating
- [ ] Format: `"... (truncated at {max_length} chars, original: {original_length})"`
