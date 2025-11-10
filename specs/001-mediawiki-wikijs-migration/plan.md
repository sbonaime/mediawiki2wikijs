# Implementation Plan: MediaWiki to Wiki.js Migration Tool

**Branch**: `001-mediawiki-wikijs-migration` | **Date**: 2025-11-10 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-mediawiki-wikijs-migration/spec.md`

**Note**: This template is filled in by the `/speckit.plan` command. See `.specify/templates/commands/plan.md` for the execution workflow.

## Summary

Build two Python command-line scripts to migrate a complete MediaWiki site to Wiki.js: an export script that retrieves all pages, images, and metadata from MediaWiki via HTTP/HTTPS API and stores them locally in a hierarchical structure; and an import script that transforms the content to markdown, renames images based on page names, and creates the pages and uploads assets to Wiki.js via its API. The solution prioritizes simplicity, supports resumable operations with checkpoints every 10 pages, handles authentication timeouts automatically, and includes dry-run and verification capabilities.

## Technical Context

**Language/Version**: Python 3.9+ (for compatibility with common distributions; 3.11+ preferred for performance)
**Primary Dependencies**: requests (2.31+), mwclient (0.10+), gql (3.4+), pypandoc (1.11+), python-dotenv (1.0+)
**Storage**: Local filesystem with hierarchical directory structure (namespace/category/page.md + separate images folder); JSON checkpoints
**Testing**: pytest with responses library for HTTP mocking, VCR.py for API recording/replay
**Target Platform**: Cross-platform (Linux, macOS, Windows) command-line tool; requires Pandoc system installation
**Project Type**: Single project (two CLI scripts with shared library code)
**Performance Goals**: Export 100+ pages in <30 minutes; 95% image download success; 90% link transformation accuracy
**Constraints**: Simplicity as primary design goal; support MediaWiki 1.13.5+; authentication timeout handling (5-minute inactivity threshold); checkpoint every 10 pages
**Scale/Scope**: Support wikis with thousands of pages and gigabytes of images; configurable link depth (default unlimited)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

**Note**: Constitution file is currently a template. Applying standard software engineering best practices:

- ✅ **Test Coverage**: pytest with unit tests for core logic, integration tests for API interactions, contract tests for MediaWiki/Wiki.js API assumptions
- ✅ **Code Quality**: pylint/flake8 for linting, type hints for clarity, clear function documentation
- ✅ **Performance**: Explicit performance targets defined in spec (SC-001 through SC-010); benchmarks for page processing rate
- ✅ **Observability**: Structured logging with configurable levels, progress indicators, detailed error log for corrupted documents
- ✅ **Versioning**: Semantic versioning for scripts, clear migration between versions
- ✅ **Simplicity**: Explicit design constraint; minimize dependencies, clear separation between export and import scripts

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit.plan command output)
├── research.md          # Phase 0 output (/speckit.plan command)
├── data-model.md        # Phase 1 output (/speckit.plan command)
├── quickstart.md        # Phase 1 output (/speckit.plan command)
├── contracts/           # Phase 1 output (/speckit.plan command)
└── tasks.md             # Phase 2 output (/speckit.tasks command - NOT created by /speckit.plan)
```

### Source Code (repository root)

```text
.env.example                    # Template for credentials configuration
requirements.txt                # Python dependencies
README.md                       # Project documentation

src/
├── export_mediawiki.py        # Export script entry point
├── import_wikijs.py           # Import script entry point
├── lib/
│   ├── __init__.py
│   ├── mediawiki_client.py    # MediaWiki API wrapper with auth handling
│   ├── wikijs_client.py       # Wiki.js GraphQL API wrapper
│   ├── content_transformer.py # Markup conversion, link transformation
│   ├── storage_manager.py     # Local file operations, checkpoint management
│   ├── image_processor.py     # Image download, renaming logic
│   ├── auth_manager.py        # Timeout detection, reconnection logic
│   ├── logger.py              # Structured logging, error log generation
│   └── config.py              # .env loading, configuration management
└── models/
    ├── __init__.py
    ├── wiki_page.py           # Page entity
    ├── image_asset.py         # Image entity
    ├── link_reference.py      # Link relationship
    └── checkpoint.py          # Checkpoint state

tests/
├── unit/
│   ├── test_content_transformer.py
│   ├── test_image_processor.py
│   ├── test_storage_manager.py
│   └── test_auth_manager.py
├── integration/
│   ├── test_mediawiki_export.py
│   └── test_wikijs_import.py
└── contract/
    ├── test_mediawiki_api.py
    └── test_wikijs_api.py

export_output/                  # Default export directory (gitignored)
├── [namespace]/
│   ├── [category]/
│   │   └── page-title.md
│   └── images/
│       └── PageName-image-001.png
└── .checkpoint                 # Checkpoint state file
```

**Structure Decision**: Single project structure chosen. Two separate CLI entry points (export_mediawiki.py, import_wikijs.py) share common library code under src/lib/. This aligns with the "two scripts" requirement while maximizing code reuse for authentication, logging, and data model handling. The models/ directory contains data entities shared between export and import operations.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
