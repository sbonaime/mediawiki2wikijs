# Tasks: MediaWiki to Wiki.js Migration Tool

**Feature Branch**: `001-mediawiki-wikijs-migration`
**Input**: Design documents from `/specs/001-mediawiki-wikijs-migration/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Tests are NOT requested in the feature specification, so test tasks are omitted. Focus is on implementation.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

Single project structure at repository root: `src/`, `tests/`, `export_output/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [X] T001 Create project directory structure (src/, src/lib/, src/models/, tests/, tests/unit/, tests/integration/, tests/contract/)
- [X] T002 Create requirements.txt with dependencies: requests>=2.31.0, mwclient>=0.10.0, gql>=3.4.0, pypandoc>=1.11, python-dotenv>=1.0.0, pytest, responses, vcrpy
- [X] T003 Create .env.example file with MediaWiki and Wiki.js configuration template (MEDIAWIKI_URL, MEDIAWIKI_USERNAME, MEDIAWIKI_PASSWORD, WIKIJS_URL, WIKIJS_API_KEY, EXPORT_DIR, CHECKPOINT_FREQUENCY, MAX_LINK_DEPTH, LOG_LEVEL)
- [X] T004 Create .gitignore with entries for .env, export_output/, venv/, __pycache__/, *.pyc, .checkpoint
- [X] T005 Create README.md with project overview, installation instructions, and links to quickstart.md

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T006 [P] Create WikiPage model in src/models/wiki_page.py with dataclass definition (id, title, namespace, content, categories, links, images, created_at, modified_at, author, revision_id, url, path, wikijs_id)
- [X] T007 [P] Create ImageAsset model in src/models/image_asset.py with dataclass definition (original_filename, renamed_filename, url, local_path, content_type, size_bytes, page_references, download_status, error_message, wikijs_url)
- [X] T008 [P] Create LinkReference model in src/models/link_reference.py with dataclass definition (source_page, target_page, link_type, anchor_text, depth)
- [X] T009 [P] Create Checkpoint model in src/models/checkpoint.py with dataclass definition and save/load methods (version, operation, timestamp, pages_processed, images_processed, current_namespace, current_page, completed_pages, config)
- [X] T010 [P] Create MigrationReport model in src/models/migration_report.py with dataclass definition and error tracking methods (operation, start_time, end_time, status, pages_total, pages_succeeded, pages_failed, pages_skipped, images_total, images_succeeded, images_failed, errors, warnings)
- [X] T011 Create config.py in src/lib/config.py to load environment variables from .env file using python-dotenv
- [X] T012 Create logger.py in src/lib/logger.py with structured logging configuration (INFO, DEBUG, WARNING, ERROR levels) and CSV error log writer
- [X] T013 Create storage_manager.py in src/lib/storage_manager.py with filesystem operations for hierarchical directory structure (create_namespace_dir, save_page_markdown, save_image, load_export_metadata)
- [X] T014 Create auth_manager.py in src/lib/auth_manager.py with timestamp-based timeout detection (5-minute threshold) and reconnection logic for both MediaWiki and Wiki.js

**Checkpoint**: Foundation ready - user story implementation can now begin in parallel

---

## Phase 3: User Story 1 - Export Complete MediaWiki Content (Priority: P1) 🎯 MVP

**Goal**: Extract all content from MediaWiki including pages, images, and metadata, stored locally in hierarchical structure

**Independent Test**: Run export script against test MediaWiki instance and verify all pages, categories, and images are captured in export_output/ directory

### Implementation for User Story 1

- [X] T015 [P] [US1] Create mediawiki_client.py in src/lib/mediawiki_client.py with mwclient wrapper for authentication (login with username/password)
- [X] T016 [P] [US1] Implement list_all_pages method in src/lib/mediawiki_client.py to retrieve pages from specified namespaces using action=query&list=allpages with pagination
- [X] T017 [P] [US1] Implement get_page_content method in src/lib/mediawiki_client.py to fetch page wikitext using action=query&prop=revisions&rvprop=content|timestamp|user
- [X] T018 [P] [US1] Implement get_page_links method in src/lib/mediawiki_client.py to fetch internal links using action=query&prop=links
- [X] T019 [P] [US1] Implement get_page_categories method in src/lib/mediawiki_client.py to fetch category memberships using action=query&prop=categories
- [X] T020 [P] [US1] Implement get_page_images method in src/lib/mediawiki_client.py to fetch image references using action=query&prop=images
- [X] T021 [P] [US1] Implement get_image_info method in src/lib/mediawiki_client.py to fetch image download URLs using action=query&prop=imageinfo&iiprop=url|size|mime
- [X] T022 [US1] Create image_processor.py in src/lib/image_processor.py with download_image method (HTTP GET request with error handling)
- [X] T023 [US1] Implement BFS link traversal in src/lib/link_traversal.py with depth tracking (uses LinkReference model, respects MAX_LINK_DEPTH from config)
- [X] T024 [US1] Implement checkpoint save/resume logic in storage_manager.py (save every 10 pages per CHECKPOINT_FREQUENCY config, check completed_pages set to skip already processed)
- [X] T025 [US1] Create export_mediawiki.py CLI script in src/ with argument parser (--dry-run, --link-depth, --resume, --namespaces, --output, --verbose, --start-page, --checkpoint-frequency, --delay)
- [X] T026 [US1] Implement export workflow in export_mediawiki.py: load config → authenticate → list pages → export pages with BFS traversal → download images → save to disk → create checkpoint every 10 pages
- [X] T027 [US1] Add authentication timeout detection in auth_manager.py for MediaWiki (check last_request_time vs 5-minute threshold, re-login if expired)
- [X] T028 [US1] Add dry-run mode support in export_mediawiki.py (list pages and report what would be exported without downloading)
- [X] T029 [US1] Add progress feedback with logging in export_mediawiki.py (log every 10 pages processed, show namespace/category progress)
- [X] T030 [US1] Add corrupted document error handling in image_processor.py and export_mediawiki.py (catch exceptions, log to CSV with page URL and filename)
- [X] T031 [US1] Generate export_metadata.json in storage_manager.py with ExportBundle data (source_url, export_date, total_pages, total_images, namespaces, categories)
- [X] T032 [US1] Generate export_errors.csv in logger.py with error records (timestamp, page_id, page_title, error_type, error_message)
- [X] T033 [US1] Add --resume flag implementation in export_mediawiki.py to load .checkpoint file and continue from last saved state

**Checkpoint**: At this point, User Story 1 should be fully functional - export script can extract complete MediaWiki site to local filesystem

---

## Phase 4: User Story 2 - Transform and Prepare Content for Wiki.js (Priority: P2)

**Goal**: Transform exported MediaWiki content into Wiki.js compatible format with markdown conversion, image renaming, and link transformation

**Independent Test**: Provide sample MediaWiki export and verify transformation produces valid markdown files with renamed images and converted links

### Implementation for User Story 2

- [X] T034 [US2] Create content_transformer.py in src/lib/content_transformer.py with pypandoc wrapper for wikitext to markdown conversion
- [X] T035 [US2] Implement convert_wikitext_to_markdown method in content_transformer.py using pypandoc.convert_text(content, 'markdown', format='mediawiki')
- [X] T036 [US2] Implement rename_images method in image_processor.py with pattern {page-slug}-image-{sequence:03d}.{ext} (e.g., "getting-started-image-001.png")
- [X] T037 [US2] Implement transform_internal_links method in content_transformer.py to convert [[Page Name]] to [Page Name](/page-name) Wiki.js format
- [X] T038 [US2] Implement normalize_page_title method in content_transformer.py to create URL-safe paths (lowercase, replace spaces with hyphens, remove special characters)
- [X] T039 [US2] Implement update_image_references method in content_transformer.py to replace MediaWiki image syntax with markdown ![alt](renamed-filename)
- [X] T040 [US2] Implement map_categories_to_tags method in content_transformer.py to convert MediaWiki categories to Wiki.js tag array
- [X] T041 [US2] Add transformation workflow to export_mediawiki.py: after export completes, iterate pages and transform wikitext to markdown in-place
- [X] T042 [US2] Update WikiPage.content field after transformation in export_mediawiki.py (change from wikitext to markdown)
- [X] T043 [US2] Update ImageAsset.renamed_filename field after renaming in export_mediawiki.py
- [X] T044 [US2] Update storage_manager.py to save transformed markdown files with updated image references
- [X] T045 [US2] Add error handling for Pandoc conversion failures in content_transformer.py (catch pypandoc.PandocException, log to errors CSV)

**Checkpoint**: At this point, User Stories 1 AND 2 should both work - export script produces Wiki.js-ready markdown files with renamed images

---

## Phase 5: User Story 3 - Import Content to Wiki.js (Priority: P3)

**Goal**: Import transformed content into Wiki.js instance, creating pages and uploading images via GraphQL API

**Independent Test**: Import transformed content into test Wiki.js instance and verify all pages are created with correct content and images are accessible

### Implementation for User Story 3

- [X] T046 [P] [US3] Create wikijs_client.py in src/lib/wikijs_client.py with gql GraphQL client initialization (endpoint: WIKIJS_URL/graphql, auth: Bearer token)
- [X] T047 [P] [US3] Implement create_page mutation in wikijs_client.py with PageCreateInput (content, description, editor="markdown", isPublished=true, isPrivate=false, locale="en", path, tags, title)
- [X] T048 [P] [US3] Implement upload_asset mutation in wikijs_client.py with multipart request for AssetCreateInput (file, folderId) per graphql-multipart-request-spec
- [X] T049 [P] [US3] Implement list_pages query in wikijs_client.py to check existing pages (for collision detection)
- [X] T050 [P] [US3] Implement get_asset_folders query in wikijs_client.py to retrieve folderId for image uploads
- [X] T051 [US3] Create import_wikijs.py CLI script in src/ with argument parser (--source, --dry-run, --skip-existing, --force, --verbose)
- [X] T052 [US3] Implement import workflow in import_wikijs.py: load config → authenticate with API key → read export_metadata.json → load pages from disk → create pages in Wiki.js → upload images
- [X] T053 [US3] Add authentication timeout detection in auth_manager.py for Wiki.js (check last_request_time vs 5-minute threshold, create new API key if expired - requires manual intervention)
- [X] T054 [US3] Add dry-run mode support in import_wikijs.py (validate data and report what would be imported without making API calls)
- [X] T055 [US3] Add --skip-existing flag implementation in import_wikijs.py (query existing pages, skip if path already exists, log as warning)
- [X] T056 [US3] Add --force flag implementation in import_wikijs.py (use update mutation instead of create for existing pages)
- [X] T057 [US3] Implement page collision handling in import_wikijs.py (check responseResult.succeeded, if false and errorCode=1001, skip and log warning)
- [X] T058 [US3] Implement image upload error handling in import_wikijs.py (catch GraphQL errors, retry once, log failures to errors CSV)
- [X] T059 [US3] Add checkpoint save/resume logic in import_wikijs.py (save every 10 pages imported, use same Checkpoint model)
- [X] T060 [US3] Add progress feedback with logging in import_wikijs.py (log every 10 pages imported, show success/failure counts)
- [X] T061 [US3] Generate migration_report.json in import_wikijs.py using MigrationReport model (pages_succeeded, pages_failed, pages_skipped, images_succeeded, images_failed, errors, warnings)
- [X] T062 [US3] Update storage_manager.py to save import checkpoint and migration report to export directory
- [X] T063 [US3] Add --resume flag implementation in import_wikijs.py to load .checkpoint file and continue from last saved state

**Checkpoint**: At this point, User Stories 1, 2, AND 3 should all work - complete migration workflow from MediaWiki export to Wiki.js import

---

## Phase 6: User Story 4 - Verify Migration Completeness (Priority: P4)

**Goal**: Verify migration was successful by comparing source and target, checking links, images, and page counts

**Independent Test**: Run verification against both MediaWiki and Wiki.js instances and produce comparison report

### Implementation for User Story 4

- [ ] T064 [P] [US4] Implement get_page_count method in mediawiki_client.py to count total pages in specified namespaces
- [ ] T065 [P] [US4] Implement list_all_pages_summary method in wikijs_client.py to retrieve page count and paths from Wiki.js
- [ ] T066 [US4] Create verification.py in src/lib/verification.py with compare_page_counts method (MediaWiki total vs Wiki.js total)
- [ ] T067 [US4] Implement verify_images method in verification.py to check all images are accessible in Wiki.js (HTTP HEAD requests to image URLs)
- [ ] T068 [US4] Implement verify_links method in verification.py to check internal links resolve (query Wiki.js for each linked path)
- [ ] T069 [US4] Implement generate_verification_report method in verification.py using MigrationReport model (differences, broken links, missing images)
- [ ] T070 [US4] Add --verify flag to import_wikijs.py to run verification after import completes
- [ ] T071 [US4] Add standalone verification mode to import_wikijs.py (--verify-only flag to run verification without import)
- [ ] T072 [US4] Output verification report to console and save to verification_report.json in export directory

**Checkpoint**: All user stories should now be independently functional - complete migration workflow with verification

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [ ] T073 [P] Add docstrings to all modules, classes, and functions following Google Python style guide
- [ ] T074 [P] Add type hints to all function signatures in src/lib/ and src/models/
- [ ] T075 [P] Create unit tests in tests/unit/test_content_transformer.py for markdown conversion edge cases
- [ ] T076 [P] Create unit tests in tests/unit/test_image_processor.py for image renaming logic
- [ ] T077 [P] Create unit tests in tests/unit/test_storage_manager.py for checkpoint save/load
- [ ] T078 [P] Create unit tests in tests/unit/test_auth_manager.py for timeout detection logic
- [ ] T079 [P] Create integration tests in tests/integration/test_mediawiki_export.py using VCR.py for API recording
- [ ] T080 [P] Create integration tests in tests/integration/test_wikijs_import.py using responses library for mocking GraphQL
- [ ] T081 [P] Create contract tests in tests/contract/test_mediawiki_api.py to validate MediaWiki 1.13.5 API compatibility
- [ ] T082 [P] Create contract tests in tests/contract/test_wikijs_api.py to validate Wiki.js 2.x GraphQL API
- [ ] T083 Add error message improvements for common failures (authentication failed, Pandoc not found, network timeout)
- [ ] T084 Add validation for .env file completeness at startup (check required fields exist)
- [ ] T085 Add command-line help text and examples to export_mediawiki.py and import_wikijs.py using argparse
- [ ] T086 [P] Run ruff or flake8 linting on all Python files and fix issues
- [ ] T087 [P] Run pylint on all Python files and fix critical issues
- [ ] T088 Validate quickstart.md instructions by following them on clean system
- [ ] T089 Add performance logging to track page processing rate and compare against SC-001 target (100+ pages in <30 minutes)
- [ ] T090 Add memory profiling for large wiki exports (>1000 pages) to ensure reasonable resource usage

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3-6)**: All depend on Foundational phase completion
  - User Story 1 (Export): Can start after Foundational
  - User Story 2 (Transform): Depends on User Story 1 completion (needs exported data)
  - User Story 3 (Import): Depends on User Story 2 completion (needs transformed data)
  - User Story 4 (Verify): Depends on User Story 3 completion (needs imported data)
- **Polish (Phase 7)**: Depends on all user stories being complete

### User Story Dependencies

- **User Story 1 (P1 - Export)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2 - Transform)**: Depends on US1 export workflow - Should be integrated into export script
- **User Story 3 (P3 - Import)**: Depends on US1+US2 producing transformed markdown - Independent import script
- **User Story 4 (P4 - Verify)**: Depends on US3 import completion - Can be run independently after import

### Within Each User Story

**User Story 1 (Export)**:
1. MediaWiki client methods can be implemented in parallel (T015-T021)
2. Image processor can be built in parallel (T022)
3. Link traversal depends on MediaWiki client (T023 depends on T015-T020)
4. CLI script depends on all library code (T025 depends on T015-T024)
5. Workflow implementation builds on CLI script (T026-T033 sequential after T025)

**User Story 2 (Transform)**:
1. Content transformer methods can be built in parallel (T034-T040)
2. Integration into export workflow (T041-T045) depends on US1 export working

**User Story 3 (Import)**:
1. Wiki.js client methods can be built in parallel (T046-T050)
2. CLI script depends on client methods (T051 depends on T046-T050)
3. Workflow implementation (T052-T063) sequential after CLI script

**User Story 4 (Verify)**:
1. Verification methods can be built in parallel (T064-T069)
2. Integration into import script (T070-T072) depends on verification methods

### Parallel Opportunities

- **Phase 1 (Setup)**: All tasks can run in parallel (T001-T005) - different files
- **Phase 2 (Foundational)**:
  - All model files can be created in parallel (T006-T010)
  - All lib files can be created in parallel (T011-T014)
- **Phase 3 (US1)**:
  - MediaWiki client methods in parallel (T015-T021)
  - After client complete, image processor and link traversal in parallel (T022-T023)
- **Phase 4 (US2)**: All transformer methods in parallel (T034-T040)
- **Phase 5 (US3)**: Wiki.js client methods in parallel (T046-T050)
- **Phase 6 (US4)**: Verification methods in parallel (T064-T068)
- **Phase 7 (Polish)**: Most documentation and testing tasks can run in parallel (T073-T090)

---

## Parallel Example: User Story 1 (Export)

```bash
# Launch all MediaWiki client methods in parallel:
Task T015: "Create mediawiki_client.py with authentication"
Task T016: "Implement list_all_pages method"
Task T017: "Implement get_page_content method"
Task T018: "Implement get_page_links method"
Task T019: "Implement get_page_categories method"
Task T020: "Implement get_page_images method"
Task T021: "Implement get_image_info method"

# After client complete, launch in parallel:
Task T022: "Create image_processor.py with download_image method"
Task T023: "Implement BFS link traversal"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1 (Export)
4. Complete Phase 4: User Story 2 (Transform) - integrated into export
5. **STOP and VALIDATE**: Test export + transform on real MediaWiki instance
6. Export should produce Wiki.js-ready markdown files

This gives you a working exporter that produces content ready for manual import or future automation.

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 + 2 → Test export+transform → **MVP Complete** (can manually import to Wiki.js)
3. Add User Story 3 → Test import → **Automated Migration Complete**
4. Add User Story 4 → Test verification → **Production Ready**
5. Add Polish (Phase 7) → **Enterprise Ready**

Each phase adds value without breaking previous functionality.

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1 (Export) - T015-T033
   - Developer B: User Story 2 (Transform) - T034-T045 (starts after US1 basics done)
   - Developer C: User Story 3 (Import) - T046-T063 (starts after US2 complete)
   - Developer D: User Story 4 (Verify) - T064-T072 (starts after US3 complete)
3. All developers work on Phase 7 (Polish) together

---

## Task Summary

- **Total Tasks**: 90
- **Setup Phase**: 5 tasks
- **Foundational Phase**: 9 tasks (BLOCKING)
- **User Story 1 (Export)**: 19 tasks
- **User Story 2 (Transform)**: 12 tasks
- **User Story 3 (Import)**: 18 tasks
- **User Story 4 (Verify)**: 9 tasks
- **Polish Phase**: 18 tasks

### Tasks per User Story

- **US1 (P1 - Export)**: 19 tasks - Core value, highest priority
- **US2 (P2 - Transform)**: 12 tasks - Essential for Wiki.js compatibility
- **US3 (P3 - Import)**: 18 tasks - Completes automation
- **US4 (P4 - Verify)**: 9 tasks - Quality assurance

### Parallel Opportunities Identified

- **27 tasks** marked [P] for parallel execution across phases
- Phase 2 (Foundational): 5 parallel model tasks, 4 parallel lib tasks
- Phase 3 (US1): 7 parallel MediaWiki client methods
- Phase 4 (US2): 7 parallel transformer methods
- Phase 5 (US3): 5 parallel Wiki.js client methods
- Phase 6 (US4): 2 parallel verification methods
- Phase 7 (Polish): 14 parallel documentation/testing tasks

### Suggested MVP Scope

**Minimum Viable Product**: User Stories 1 + 2 (Export + Transform)
- **31 tasks** (Setup + Foundational + US1 + US2)
- **Deliverable**: Working MediaWiki exporter producing Wiki.js-compatible markdown
- **Value**: Enables migration even if import is manual
- **Validation**: Run against production MediaWiki, verify markdown output

---

## Notes

- [P] tasks = different files, no dependencies - can run in parallel
- [Story] label maps task to specific user story for traceability
- User Story 2 (Transform) is integrated into export script for simplicity
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- **No test tasks included** - feature spec does not request TDD approach
- Tests in Phase 7 (Polish) are optional enhancements, not blocking
