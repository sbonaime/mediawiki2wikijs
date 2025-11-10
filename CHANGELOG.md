# Changelog

All notable changes to the MediaWiki to Wiki.js Migration Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned Features
- Verification tools for migration completeness (Phase 6)
- Comprehensive test suite (Phase 7)
- CI/CD pipeline setup
- Docker container support

## [0.9.0] - 2025-11-10

### Added (MVP Release - 70% Complete)

#### Phase 1-2: Setup and Foundation
- Project directory structure with `src/`, `tests/`, `specs/`
- Requirements.txt with core dependencies (requests, mwclient, gql, pypandoc, python-dotenv)
- Configuration management via `.env` file
- Comprehensive logging with CSV error reports
- Data models: WikiPage, ImageAsset, LinkReference, Checkpoint, MigrationReport
- Authentication manager with timeout detection (5-minute threshold)
- Storage manager for hierarchical file system organization

#### Phase 3: MediaWiki Export (User Story 1)
- **MediaWiki API Client** (`src/lib/mediawiki_client.py`)
  - Authentication with username/password
  - Support for MediaWiki 1.13.5+
  - List pages by namespace with pagination
  - Fetch page content, links, categories, images
  - Download image files with metadata
- **BFS Link Traversal** (`src/lib/link_traversal.py`)
  - Configurable link depth limiting
  - Cycle detection with visited page tracking
  - Link reference collection for relationship mapping
- **Image Processor** (`src/lib/image_processor.py`)
  - HTTP image download with streaming
  - Timeout handling and error recovery
  - Page-based image renaming pattern
- **Export CLI Script** (`export.py`)
  - Command-line argument parsing (12+ options)
  - Two export modes: namespace listing or BFS traversal
  - Checkpoint save/resume every 10 pages
  - Dry-run mode for preview
  - Progress logging and error tracking
  - Export metadata generation

#### Phase 4: Content Transformation (User Story 2)
- **Content Transformer** (`src/lib/content_transformer.py`)
  - Pandoc-based wikitext→markdown conversion
  - Internal link transformation `[[Page]]` → `[Page](/page)`
  - Image reference updating with renamed filenames
  - Category to tag mapping
  - URL-safe path normalization
- **Integration into Export Workflow**
  - Optional `--transform` flag for automatic conversion
  - Batch transformation support
  - Error handling for Pandoc failures

#### Phase 5: Wiki.js Import (User Story 3)
- **Wiki.js GraphQL Client** (`src/lib/wikijs_client.py`)
  - GraphQL API authentication with Bearer token
  - `pages.create` mutation for page creation
  - `pages.update` mutation for collision handling
  - Asset upload via REST multipart API
  - Page listing and path-based lookup
  - Asset folder management
- **Import CLI Script** (`import_wikijs.py`)
  - Command-line argument parsing (13+ options)
  - Import workflow: config → auth → load → import → upload
  - Collision strategies: skip (default) or update (--force)
  - Checkpoint save/resume every 10 pages
  - Dry-run mode for validation
  - Progress logging and migration report
  - Exit codes for success/failure tracking

### Technical Features
- **Authentication Management**
  - Automatic timeout detection (5 minutes)
  - Session reconnection for MediaWiki
  - API key management for Wiki.js
- **Checkpoint System**
  - JSON-based state persistence
  - Resume from interruption
  - Completed page tracking to avoid duplicates
- **Error Handling**
  - CSV error logging with timestamps
  - Exception catching with detailed messages
  - Graceful failure with partial success tracking
- **Progress Tracking**
  - Log every 10 pages processed
  - Success/failure/skipped counts
  - Duration and performance metrics

### Documentation
- Comprehensive README.md with quickstart
- Detailed quickstart guide (quickstart.md)
- Feature specification (spec.md)
- Implementation plan (plan.md)
- Research documentation (research.md)
- Data model definitions (data-model.md)
- Task breakdown with progress tracking (tasks.md)
- API contracts for MediaWiki and Wiki.js

### Project Structure
```
src/
├── export.py (500 lines)
├── import_wikijs.py (443 lines)
├── lib/
│   ├── mediawiki_client.py (375 lines)
│   ├── wikijs_client.py (456 lines)
│   ├── content_transformer.py (253 lines)
│   ├── image_processor.py (145 lines)
│   ├── link_traversal.py (145 lines)
│   ├── storage_manager.py (200+ lines)
│   ├── auth_manager.py (150+ lines)
│   ├── config.py (100+ lines)
│   └── logger.py (100+ lines)
└── models/
    ├── wiki_page.py
    ├── image_asset.py
    ├── link_reference.py
    ├── checkpoint.py
    └── migration_report.py
```

## Implementation Progress

### Completed (63/90 tasks)
- ✅ Phase 1: Setup (5/5 tasks)
- ✅ Phase 2: Foundational (9/9 tasks)
- ✅ Phase 3: Export (19/19 tasks)
- ✅ Phase 4: Transform (12/12 tasks)
- ✅ Phase 5: Import (18/18 tasks)

### Pending (27/90 tasks)
- ⏳ Phase 6: Verification (0/9 tasks)
- ⏳ Phase 7: Polish & Tests (0/18 tasks)

## [0.1.0] - 2025-11-10

### Added
- Initial project setup
- Specification documents
- Design planning

---

## Version History

- **0.9.0** - MVP Release: Complete migration workflow (export + transform + import)
- **0.1.0** - Initial planning and specification

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on how to contribute to this project.
