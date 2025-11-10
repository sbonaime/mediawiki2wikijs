# Research: MediaWiki to Wiki.js Migration Tool

**Feature**: 001-mediawiki-wikijs-migration
**Date**: 2025-11-10
**Phase**: 0 (Outline & Research)

## Purpose

Resolve technical unknowns from the implementation plan and establish best practices for MediaWiki API integration, Wiki.js GraphQL API usage, markdown conversion, and Python project structure for CLI tools.

---

## Decision 1: Primary Dependencies for HTTP and API Interaction

**Context**: Need to interact with MediaWiki API (REST/action API) and Wiki.js GraphQL API over HTTP/HTTPS.

**Decision**:
- **requests** (2.31+) for HTTP operations
- **mwclient** (0.10+) for high-level MediaWiki API wrapper (supports MW 1.13.5+)
- **gql** (3.4+) for Wiki.js GraphQL client
- **python-dotenv** (1.0+) for .env file handling

**Rationale**:
- `requests` is the de facto standard for HTTP in Python, simple and reliable
- `mwclient` provides robust MediaWiki API abstraction with built-in pagination, authentication, and error handling; has been stable for years and supports legacy MediaWiki versions
- `gql` provides type-safe GraphQL queries with good error handling
- `python-dotenv` is lightweight standard for .env configuration

**Alternatives Considered**:
- **httpx** (modern async HTTP): Rejected because async complexity contradicts simplicity constraint; sync operations sufficient for CLI tool
- **Manual MediaWiki API calls with requests**: Rejected because `mwclient` handles pagination, session management, and API version differences robustly
- **wiki** library: Rejected because it's designed for Wikipedia specifically, not self-hosted MediaWiki instances

---

## Decision 2: Markdown Conversion Library

**Context**: Need to convert MediaWiki wikitext markup to markdown format compatible with Wiki.js.

**Decision**: **pandoc** (via pypandoc Python wrapper, 1.11+) for markup conversion

**Rationale**:
- Pandoc is the most mature and comprehensive markup converter, handles MediaWiki syntax well
- Supports MediaWiki wikitext → markdown conversion natively
- `pypandoc` provides simple Python interface
- Widely used, well-documented, actively maintained

**Alternatives Considered**:
- **wikitextparser**: Python library for parsing wikitext, but requires manual markdown generation (more complexity)
- **mwparserfromhell**: Good wikitext parser but doesn't generate markdown directly
- **Custom regex-based converter**: Rejected due to complexity and incomplete coverage of MediaWiki syntax edge cases

**Implementation Note**: Pandoc must be installed as system dependency; document in README prerequisites.

---

## Decision 3: Authentication Timeout Detection Strategy

**Context**: Need to detect when MediaWiki/Wiki.js sessions have timed out after 5 minutes of inactivity and reconnect automatically.

**Decision**: Track last successful API call timestamp; check elapsed time before each operation; re-authenticate if >5 minutes elapsed

**Rationale**:
- Simple to implement with datetime tracking
- Proactive rather than reactive (prevents timeout errors)
- Works regardless of server-side session timeout configuration
- No need to parse session tokens or complex auth state

**Alternatives Considered**:
- **Catch 401/403 errors and retry**: Rejected because it wastes one API call per timeout and complicates error handling
- **Keep-alive pings**: Rejected because it adds unnecessary network traffic and complexity
- **Token introspection**: Rejected because not all MediaWiki/Wiki.js versions expose token expiry information

**Implementation Note**: Decorator pattern on API wrapper methods to automatically check timeout and re-authenticate.

---

## Decision 4: Checkpoint File Format

**Context**: Need to store checkpoint state to resume operations after interruptions (every 10 pages).

**Decision**: JSON file (`.checkpoint`) with schema:
```json
{
  "version": "1.0",
  "operation": "export" | "import",
  "timestamp": "ISO-8601",
  "progress": {
    "pages_processed": 42,
    "images_processed": 156,
    "current_namespace": "Main",
    "current_page": "Page Title",
    "completed_pages": ["Page1", "Page2", ...]
  },
  "config": {
    "link_depth": 3,
    "source_url": "https://wiki.example.com"
  }
}
```

**Rationale**:
- JSON is human-readable for debugging, widely supported
- Simple schema covers essential resume information
- `completed_pages` list prevents duplicate processing
- `config` snapshot ensures resume uses original parameters

**Alternatives Considered**:
- **SQLite database**: Rejected as over-engineering for simple resume state
- **Pickle**: Rejected due to security concerns and lack of human readability
- **YAML**: Rejected because JSON is simpler and doesn't require additional dependency

---

## Decision 5: Link Depth Implementation Approach

**Context**: Need configurable link depth with default unlimited (follow all links).

**Decision**: Breadth-first traversal with depth tracking; command-line option `--link-depth N` (default: `None` = unlimited)

**Rationale**:
- BFS ensures all pages at depth N are captured before proceeding to N+1
- Natural fit for wiki link graph traversal
- Easy to implement depth limit check in BFS loop
- Prevents stack overflow for deep link chains (vs DFS)

**Alternatives Considered**:
- **Depth-first search**: Rejected because it could process very deep chains before breadth, leading to unbalanced progress
- **Separate "follow links" boolean**: Rejected because depth gives more control

**Implementation Note**: Track `(page, depth)` tuples in queue; skip adding links if current depth >= max_depth.

---

## Decision 6: Dry-Run Implementation

**Context**: Need dry-run mode that simulates operations without making actual changes to Wiki.js.

**Decision**: Command-line flag `--dry-run`; wrap all Wiki.js API write operations in conditional checks; log intended actions at INFO level

**Rationale**:
- Standard CLI pattern for dry-run
- Simple conditional logic around API calls
- Logging provides visibility into what would happen
- No need for complex mock infrastructure

**Implementation Note**: Import script only (export always writes to local filesystem).

---

## Decision 7: Error Log Format for Corrupted Documents

**Context**: Need to log corrupted/inaccessible documents with page URL and filename.

**Decision**: Separate CSV file (`export_errors.csv`) with columns: `timestamp, page_url, filename, error_type, error_message`

**Rationale**:
- CSV is simple, parseable, spreadsheet-compatible for review
- Separate file prevents cluttering main log
- Structured format allows automated analysis
- Human-readable for manual review

**Alternatives Considered**:
- **JSON lines**: Rejected as less accessible for non-technical users
- **Append to main log**: Rejected to keep error summary separate and easily filterable

---

## Decision 8: Testing Strategy

**Context**: Need pytest tests covering unit, integration, and contract levels.

**Decision**:
- **Unit tests**: Mock API responses, test transformation logic, checkpoint management
- **Integration tests**: Use `responses` library to mock HTTP, test full export/import flows
- **Contract tests**: Real API calls to test MediaWiki 1.13.5+ instance (if available) or VCR.py for recording

**Rationale**:
- Layered testing matches risk profile
- `responses` library provides simple HTTP mocking without network
- VCR.py allows recording real API interactions for regression testing
- Contract tests validate assumptions about external APIs

**Alternatives Considered**:
- **Docker-based MediaWiki/Wiki.js for testing**: Ideal but complex setup; deferred to CI/CD
- **Manual testing only**: Rejected due to regression risk

---

## Decision 9: MediaWiki 1.13.5 Compatibility Strategy

**Context**: Must support MediaWiki 1.13.5 (released 2009), which predates some modern API features.

**Decision**: Use `mwclient` library which abstracts API version differences; test against feature detection pattern; document minimum API requirements

**Rationale**:
- MW 1.13.5 has basic action API (api.php) with list, query, and edit actions
- `mwclient` handles protocol differences across versions
- Feature detection allows graceful degradation (e.g., skip categories if unsupported)

**Compatibility Notes**:
- MW 1.13.5 supports: `action=query`, `action=login`, `list=allpages`, `prop=revisions`, `prop=images`
- May lack: Advanced prop like `pageprops`, `pageimages`; some meta information
- Strategy: Test required API endpoints; log warnings if optional features unavailable

**Alternatives Considered**:
- **Require MW 1.23+**: Rejected because user explicitly requested 1.13.5 support
- **Separate code paths per version**: Rejected as over-complex; feature detection is cleaner

---

## Decision 10: Wiki.js API Version and Authentication

**Context**: Need to authenticate and interact with Wiki.js GraphQL API.

**Decision**: Target Wiki.js 2.x GraphQL API; use API key authentication (stored in .env); use `gql` with `requests` transport

**Rationale**:
- Wiki.js 2.x is current stable version with mature GraphQL API
- API keys are simpler than OAuth for CLI tools
- `gql` library provides query validation and type safety

**GraphQL Queries Needed**:
- `pages.create`: Create new page
- `assets.upload`: Upload images
- `pages.list`: List existing pages (for collision detection)

**Alternatives Considered**:
- **Wiki.js REST API**: Rejected because GraphQL is the primary/recommended API for Wiki.js 2.x
- **Username/password auth**: Rejected because API keys are more secure for automation

---

## Summary of Resolved Clarifications

All "NEEDS CLARIFICATION" items from Technical Context now resolved:

| Unknown | Resolution |
|---------|------------|
| Primary Dependencies | requests, mwclient, gql, python-dotenv, pypandoc |
| Testing Framework | pytest with responses and VCR.py |
| Markdown Conversion | Pandoc via pypandoc |
| Auth Timeout Strategy | Timestamp tracking with 5-minute threshold |
| Checkpoint Format | JSON with progress and config snapshot |
| Link Depth Implementation | BFS traversal with depth tracking |
| Dry-Run Implementation | Conditional API call execution with logging |
| Error Log Format | CSV with structured error information |
| MW 1.13.5 Compatibility | mwclient with feature detection |
| Wiki.js API Approach | GraphQL 2.x with API key authentication |

## Next Steps

Proceed to Phase 1: Design artifacts (data-model.md, contracts/, quickstart.md)
