# Feature Specification: MediaWiki to Wiki.js Migration Tool

**Feature Branch**: `001-mediawiki-wikijs-migration`
**Created**: 2025-11-10
**Status**: Draft
**Input**: User description: "Create a script that can help me export a complete mediawiki site and import the result to a new wikijs site. keep the same page and links organisation. keep images. rename images base on the page name. the mediawiki and the wikijs will be access through http/https if possible"

## Clarifications

### Session 2025-11-10

- Q: What format should MediaWiki pages be created in? → A: Markdown format
- Q: How should authentication be handled? → A: Script checks authentication on both MediaWiki and Wiki.js at startup; implements automatic reconnection if authentication times out
- Q: How should redirects/moved pages be handled? → A: Build new page structure in the simplest possible way
- Q: How should corrupted documents be handled? → A: Create a log file with page URL and filename for each corrupted document
- Q: What implementation language should be used? → A: Python, with simplicity as primary constraint
- Q: How should exported data be stored? → A: Locally in files with clear hierarchical structure
- Q: Should link depth be configurable? → A: Yes, option to follow a certain number of links depth
- Q: Should a dry-run mode be supported? → A: Yes
- Q: Should export and import be separate? → A: Two scripts: one for exporting, one for importing
- Q: How should credentials be provided? → A: Username and password for both Wiki.js and MediaWiki provided via .env file
- Q: How should the exported content be organized in the local filesystem? → A: Hierarchical by namespace - Directory per namespace, subdirectories for categories, pages as markdown files, separate images folder
- Q: How long should the script wait before considering an authentication session timed out and attempting reconnection? → A: 5 minutes of inactivity
- Q: How should the import script handle existing pages in Wiki.js with the same name as pages being imported? → A: Skip pages that already exist and log them as warnings
- Q: What should be the default link depth when the user doesn't specify a limit? → A: Unlimited (follow all links)
- Q: How frequently should the scripts create checkpoints during export/import operations? → A: Every 10 pages processed
- Q: What is the minimum MediaWiki version that must be supported? → A: MediaWiki 1.13.5 or later

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Export Complete MediaWiki Content (Priority: P1)

An administrator needs to extract all content from an existing MediaWiki installation including pages, images, and metadata. The administrator provides the MediaWiki site URL and authentication credentials, runs the export command, and receives a structured export containing all wiki pages with their complete revision history, metadata, and relationships preserved.

**Why this priority**: Without a complete and accurate export, no migration can occur. This is the foundational capability that enables all subsequent migration steps.

**Independent Test**: Can be fully tested by running the export against a test MediaWiki instance and verifying that all pages, categories, and images are captured in the export output without requiring the import step.

**Acceptance Scenarios**:

1. **Given** a MediaWiki site accessible via HTTP/HTTPS with valid credentials, **When** the user runs the export command with the site URL, **Then** all wiki pages are extracted with their current content, title, and namespace information
2. **Given** a MediaWiki site with images embedded in pages, **When** the export runs, **Then** all images are downloaded and catalogued with references to their source pages
3. **Given** a MediaWiki site with internal wiki links between pages, **When** the export completes, **Then** all link relationships are captured and preserved in the export data structure
4. **Given** a MediaWiki site with category organization, **When** the export runs, **Then** all category memberships and hierarchies are recorded in the export
5. **Given** an export operation that encounters network errors, **When** connectivity is temporarily lost, **Then** the export resumes from the last successful checkpoint without re-downloading completed content

---

### User Story 2 - Transform and Prepare Content for Wiki.js (Priority: P2)

An administrator has exported MediaWiki content and needs to transform it into a format compatible with Wiki.js, including converting markup syntax, reorganizing images with meaningful names, and mapping the page hierarchy.

**Why this priority**: This transformation step is essential to ensure content displays correctly in Wiki.js and maintains its organizational structure. It bridges the gap between MediaWiki and Wiki.js formats.

**Independent Test**: Can be tested by providing a sample MediaWiki export and verifying the transformation produces valid Wiki.js import files with correctly renamed images and preserved link structure, without requiring actual import to Wiki.js.

**Acceptance Scenarios**:

1. **Given** an exported MediaWiki page with MediaWiki markup syntax, **When** the transformation runs, **Then** the markup is converted to Wiki.js compatible markdown format
2. **Given** exported images with generic MediaWiki filenames, **When** the transformation processes them, **Then** images are renamed based on the page name they appear on (e.g., "PageName-image-001.png")
3. **Given** internal wiki links in MediaWiki format ([[Page Name]]), **When** the transformation runs, **Then** links are converted to Wiki.js link format while preserving the same target pages
4. **Given** a MediaWiki page hierarchy with categories and namespaces, **When** the transformation runs, **Then** the structure is mapped to Wiki.js path-based organization
5. **Given** pages with special characters or spaces in titles, **When** the transformation runs, **Then** page paths are normalized to URL-safe formats while maintaining readability

---

### User Story 3 - Import Content to Wiki.js (Priority: P3)

An administrator has transformed MediaWiki content and needs to import it into a new or existing Wiki.js installation, creating all pages, uploading images, and establishing the organizational structure.

**Why this priority**: This completes the migration by actually populating the target Wiki.js instance. It depends on the export and transformation being complete and correct.

**Independent Test**: Can be tested by importing transformed content into a test Wiki.js instance and verifying that all pages are created, images are accessible, and internal links navigate correctly.

**Acceptance Scenarios**:

1. **Given** transformed Wiki.js content and a target Wiki.js instance accessible via HTTP/HTTPS, **When** the user runs the import command with authentication credentials, **Then** all pages are created in Wiki.js with correct content and titles
2. **Given** renamed images from the transformation step, **When** the import runs, **Then** all images are uploaded to Wiki.js and page content references are updated to point to the new image locations
3. **Given** transformed internal links, **When** the import completes, **Then** all wiki links navigate to the correct pages within Wiki.js
4. **Given** a page hierarchy from the transformation, **When** the import runs, **Then** the Wiki.js page tree reflects the original MediaWiki organization structure
5. **Given** an import operation that encounters errors on specific pages, **When** failures occur, **Then** the import continues with remaining pages and produces a detailed error report listing failed pages and reasons

---

### User Story 4 - Verify Migration Completeness (Priority: P4)

An administrator has completed the import and needs to verify that the migration was successful, including checking that all pages exist, links work, images display correctly, and the organizational structure matches the source.

**Why this priority**: Verification provides confidence that the migration succeeded and identifies any issues that need manual correction before decommissioning the old MediaWiki site.

**Independent Test**: Can be tested by running validation checks against both the source MediaWiki and target Wiki.js instances and producing a comparison report.

**Acceptance Scenarios**:

1. **Given** a completed import to Wiki.js, **When** the user runs the verification command, **Then** a report is generated comparing page counts between MediaWiki and Wiki.js
2. **Given** pages with embedded images, **When** verification runs, **Then** the report confirms all images are accessible in Wiki.js and display correctly
3. **Given** pages with internal links, **When** verification runs, **Then** the report identifies any broken links that need correction
4. **Given** the original MediaWiki category structure, **When** verification runs, **Then** the report confirms the Wiki.js page hierarchy matches the intended organization

---

### Edge Cases

- What happens when MediaWiki requires authentication but credentials are invalid or expired? (Script validates at startup and fails fast with clear error message)
- What happens when authentication sessions time out during long-running operations? (Script detects timeout and automatically reconnects/re-authenticates)
- How does the system handle MediaWiki pages with identical titles in different namespaces?
- What happens when image files have duplicate names across different pages?
- How does the tool handle very large wikis with thousands of pages and gigabytes of images?
- What happens when Wiki.js already has pages with the same names as imported pages? (Script skips existing pages and logs them as warnings)
- What happens when link depth limit is reached during export? (Script stops following links beyond configured depth)
- What happens in dry-run mode? (Script simulates operations and reports what would be done without making changes)
- How does the system handle MediaWiki templates and transclusion (template includes)?
- What happens when network connections are interrupted during long-running exports or imports?
- How does the tool handle MediaWiki extensions or custom markup that has no Wiki.js equivalent?
- What happens when image files or pages are corrupted or inaccessible in MediaWiki? (Script logs URL and filename to error log and continues with remaining content)
- How does the system handle MediaWiki redirects and page moves? (Script builds new page structure using simplest approach)

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST be implemented in Python with simplicity as primary design constraint
- **FR-002**: System MUST consist of two separate scripts: one for export operations and one for import operations
- **FR-003**: System MUST read credentials (username and password) for MediaWiki and Wiki.js from a .env file
- **FR-004**: System MUST connect to MediaWiki instances via HTTP or HTTPS protocols using standard MediaWiki API endpoints
- **FR-004a**: System MUST support MediaWiki version 1.13.5 or later
- **FR-005**: System MUST connect to Wiki.js instances via HTTP or HTTPS using the Wiki.js API
- **FR-006**: System MUST validate authentication to both MediaWiki and Wiki.js at script startup before proceeding with operations
- **FR-007**: System MUST automatically reconnect and re-authenticate if authentication sessions time out (defined as 5 minutes of inactivity) during operations
- **FR-008**: System MUST export all wiki pages including their current content, titles, namespaces, and category memberships
- **FR-009**: System MUST store exported data locally in a hierarchical directory structure organized by namespace (one directory per namespace), with subdirectories for categories, pages stored as markdown files, and a separate images folder
- **FR-010**: System MUST download all images referenced in MediaWiki pages and maintain the association between images and their source pages
- **FR-011**: System MUST extract and preserve internal wiki link relationships between pages
- **FR-012**: System MUST support a configurable link depth option to limit how many levels of linked pages to follow during export (default: unlimited, follow all links)
- **FR-013**: System MUST convert MediaWiki markup syntax to markdown format
- **FR-014**: System MUST rename exported images based on their associated page names using a consistent naming convention (e.g., "PageName-image-001.png")
- **FR-015**: System MUST transform MediaWiki internal links to equivalent Wiki.js link format
- **FR-016**: System MUST handle MediaWiki redirects and moved pages by building the new page structure in the simplest possible way
- **FR-017**: System MUST detect corrupted or inaccessible documents and log the page URL and filename to a dedicated error log file
- **FR-018**: System MUST map MediaWiki organizational structure (categories, namespaces) to Wiki.js path-based page hierarchy
- **FR-019**: System MUST create pages in Wiki.js with transformed markdown content from MediaWiki
- **FR-020**: System MUST upload renamed images to Wiki.js and update page content references to use the new image locations
- **FR-021**: System MUST support a dry-run mode that simulates operations without making actual changes to Wiki.js
- **FR-022**: System MUST skip pages that already exist in Wiki.js and log them as warnings, continuing with remaining content
- **FR-023**: System MUST handle import errors gracefully by logging failures and continuing with remaining content
- **FR-024**: System MUST provide progress feedback during long-running export and import operations
- **FR-025**: System MUST generate a verification report comparing source and target content
- **FR-026**: System MUST support resumable operations that can continue from checkpoints after interruptions, creating checkpoints every 10 pages processed
- **FR-027**: System MUST normalize page titles and paths to be compatible with Wiki.js URL requirements
- **FR-028**: System MUST handle special characters, spaces, and non-ASCII characters in page titles and image names
- **FR-029**: System MUST log all operations with sufficient detail for troubleshooting and audit purposes

### Key Entities

- **Wiki Page**: Represents a content page with title, content body, namespace, categories, creation/modification metadata, and relationships to other pages and images
- **Image Asset**: Represents an image file with original filename, content, size, associated page references, and transformed filename for the target system
- **Link Reference**: Represents a connection between pages, including source page, target page, link type (internal/category), and anchor text
- **Export Bundle**: Collection of extracted pages, images, link references, and organizational metadata from MediaWiki
- **Import Manifest**: Transformed content ready for Wiki.js import, including pages in markdown format, renamed images, mapped page hierarchy, and updated references
- **Migration Report**: Summary of migration activities including counts of exported/imported items, success/failure status, errors encountered, and verification results

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Administrators can export a complete MediaWiki site with 100+ pages in under 30 minutes
- **SC-002**: 100% of MediaWiki pages are successfully exported with their current content intact
- **SC-003**: 95% of MediaWiki images are successfully downloaded and associated with their source pages
- **SC-004**: 90% of internal wiki links are correctly transformed and remain functional after import to Wiki.js
- **SC-005**: Administrators can complete the full migration workflow (export, transform, import) with fewer than 5 manual intervention steps
- **SC-006**: Migration verification reports accurately identify discrepancies with less than 1% false positives
- **SC-007**: The system handles network interruptions and resumes operations without requiring complete restart
- **SC-008**: Transformed content displays correctly in Wiki.js without rendering errors for 95% of pages
- **SC-009**: Image naming convention produces unique, readable filenames that resolve naming conflicts
- **SC-010**: Migration logs provide sufficient detail to troubleshoot 90% of issues without additional debugging

## Assumptions

- MediaWiki sites are running version 1.13.5 or later and are accessible via their standard API endpoints (api.php)
- Wiki.js instances use the standard GraphQL API available in Wiki.js 2.x and later
- Users have administrative access or appropriate API credentials for both source and target systems
- Users can provide credentials via .env file in the format expected by the scripts
- Python runtime environment is available on the system where scripts will run
- Network connectivity is generally stable, though the tool handles temporary interruptions and authentication timeouts
- MediaWiki content uses standard markup without extensive custom extensions
- The target Wiki.js instance has sufficient storage for all migrated images
- Page titles in MediaWiki are reasonably unique within their namespace context
- Local filesystem has sufficient storage for the complete exported content before import begins
- Standard authentication methods (username/password) are sufficient for both systems