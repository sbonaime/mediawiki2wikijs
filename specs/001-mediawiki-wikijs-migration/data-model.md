# Data Model: MediaWiki to Wiki.js Migration Tool

**Feature**: 001-mediawiki-wikijs-migration
**Date**: 2025-11-10
**Phase**: 1 (Design)

## Overview

This document defines the core data entities for the MediaWiki to Wiki.js migration tool. These entities represent the content extracted from MediaWiki, transformed during processing, and imported into Wiki.js.

---

## Entity: WikiPage

**Purpose**: Represents a single wiki page with content, metadata, and relationships.

### Attributes

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `id` | str | Required, unique | MediaWiki page ID |
| `title` | str | Required | Page title as it appears in MediaWiki |
| `namespace` | str | Required | MediaWiki namespace (e.g., "Main", "User", "Help") |
| `content` | str | Required | Raw page content (wikitext for export, markdown after transformation) |
| `categories` | List[str] | Optional | List of category names the page belongs to |
| `links` | List[str] | Optional | List of page titles this page links to |
| `images` | List[str] | Optional | List of image filenames referenced in the page |
| `created_at` | datetime | Optional | Page creation timestamp |
| `modified_at` | datetime | Optional | Last modification timestamp |
| `author` | str | Optional | Last contributor username |
| `revision_id` | str | Optional | MediaWiki revision ID |
| `url` | str | Required | Full URL to the page in MediaWiki |
| `path` | str | Optional | Local filesystem path (relative) after export |
| `wikijs_id` | str | Optional | Wiki.js page ID after import |

### Relationships

- **Has many** ImageAsset (via `images` field)
- **Has many** LinkReference (as source page)
- **Belongs to** Category (via `categories` field)

### Validation Rules

- `title` must not be empty
- `namespace` defaults to "Main" if not specified
- `url` must be valid HTTP/HTTPS URL
- `content` must not be null (can be empty string for empty pages)

### State Transitions

1. **Exported**: Page retrieved from MediaWiki API, has wikitext content
2. **Transformed**: Content converted to markdown, links updated, images renamed
3. **Imported**: Page created in Wiki.js, has `wikijs_id`
4. **Verified**: Confirmed to exist in Wiki.js and match source

---

## Entity: ImageAsset

**Purpose**: Represents an image file associated with wiki pages.

### Attributes

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `original_filename` | str | Required | Filename in MediaWiki |
| `renamed_filename` | str | Optional | New filename based on page name (e.g., "PageName-image-001.png") |
| `url` | str | Required | Full URL to download image from MediaWiki |
| `local_path` | str | Optional | Local filesystem path after download |
| `content_type` | str | Optional | MIME type (e.g., "image/png", "image/jpeg") |
| `size_bytes` | int | Optional | File size in bytes |
| `page_references` | List[str] | Required | List of page titles that reference this image |
| `download_status` | str | Required | Status: "pending", "downloaded", "failed", "uploaded" |
| `error_message` | str | Optional | Error details if download_status is "failed" |
| `wikijs_url` | str | Optional | URL in Wiki.js after upload |

### Relationships

- **Referenced by many** WikiPage (via `page_references`)

### Validation Rules

- `original_filename` must not be empty
- `url` must be valid HTTP/HTTPS URL
- `size_bytes` must be positive if specified
- `download_status` must be one of: ["pending", "downloaded", "failed", "uploaded"]
- `renamed_filename` follows pattern: `{page_name}-image-{sequence:03d}.{ext}`

### State Transitions

1. **Pending**: Identified during page export
2. **Downloaded**: File retrieved and saved locally
3. **Failed**: Download encountered error (logged to error CSV)
4. **Uploaded**: File successfully uploaded to Wiki.js

---

## Entity: LinkReference

**Purpose**: Represents a link from one page to another within the wiki.

### Attributes

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `source_page` | str | Required | Title of the page containing the link |
| `target_page` | str | Required | Title of the page being linked to |
| `link_type` | str | Required | Type: "internal", "category", "redirect" |
| `anchor_text` | str | Optional | Display text of the link (if different from target) |
| `depth` | int | Required | Link depth from starting page (for depth limiting) |

### Relationships

- **Belongs to** WikiPage (source_page)
- **References** WikiPage (target_page)

### Validation Rules

- `source_page` and `target_page` must not be empty
- `link_type` must be one of: ["internal", "category", "redirect"]
- `depth` must be non-negative integer

### Usage

- Used during export to track which pages need to be followed (BFS traversal)
- Used during transformation to convert MediaWiki link syntax to Wiki.js format
- Used for verification to ensure link integrity post-migration

---

## Entity: ExportBundle

**Purpose**: Container for complete export data from MediaWiki.

### Attributes

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `source_url` | str | Required | MediaWiki site URL |
| `export_date` | datetime | Required | Timestamp of export operation |
| `pages` | Dict[str, WikiPage] | Required | Dictionary of page_id → WikiPage |
| `images` | Dict[str, ImageAsset] | Required | Dictionary of filename → ImageAsset |
| `links` | List[LinkReference] | Required | List of all link relationships |
| `namespaces` | List[str] | Required | List of namespaces encountered |
| `categories` | Dict[str, List[str]] | Required | Category → [page titles] mapping |
| `total_pages` | int | Required | Count of pages exported |
| `total_images` | int | Required | Count of images downloaded |
| `link_depth_limit` | int | Optional | Maximum link depth used (None = unlimited) |

### Methods

- `save_to_disk(output_dir)`: Serialize export to filesystem hierarchy
- `load_from_disk(output_dir)`: Deserialize export from filesystem
- `add_page(page)`: Add page to bundle
- `add_image(image)`: Add image to bundle
- `add_link(link)`: Add link reference

---

## Entity: Checkpoint

**Purpose**: Stores progress state for resumable operations.

### Attributes

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `version` | str | Required | Checkpoint format version (e.g., "1.0") |
| `operation` | str | Required | "export" or "import" |
| `timestamp` | datetime | Required | When checkpoint was created |
| `pages_processed` | int | Required | Count of pages completed |
| `images_processed` | int | Required | Count of images completed |
| `current_namespace` | str | Optional | Namespace currently being processed |
| `current_page` | str | Optional | Page currently being processed |
| `completed_pages` | Set[str] | Required | Set of page IDs already processed |
| `config` | Dict | Required | Configuration snapshot (URL, depth, etc.) |

### Methods

- `save(filepath)`: Serialize to JSON file
- `load(filepath)`: Deserialize from JSON file
- `should_skip(page_id)`: Check if page already processed

### Validation Rules

- `operation` must be "export" or "import"
- `pages_processed` must match length of `completed_pages`
- Checkpoint saved every 10 pages per FR-026

---

## Entity: MigrationReport

**Purpose**: Summary of migration activities and results.

### Attributes

| Field | Type | Constraints | Description |
|-------|------|-------------|-------------|
| `operation` | str | Required | "export", "import", or "verification" |
| `start_time` | datetime | Required | Operation start timestamp |
| `end_time` | datetime | Optional | Operation completion timestamp |
| `status` | str | Required | "in_progress", "completed", "failed" |
| `pages_total` | int | Required | Total pages to process |
| `pages_succeeded` | int | Required | Pages successfully processed |
| `pages_failed` | int | Required | Pages that encountered errors |
| `pages_skipped` | int | Required | Pages skipped (e.g., already exist in Wiki.js) |
| `images_total` | int | Required | Total images to process |
| `images_succeeded` | int | Required | Images successfully processed |
| `images_failed` | int | Required | Images that encountered errors |
| `errors` | List[Dict] | Required | List of error records with page/image details |
| `warnings` | List[Dict] | Required | List of warnings (e.g., skipped pages) |

### Methods

- `add_error(page_id, error_message)`: Record an error
- `add_warning(page_id, warning_message)`: Record a warning
- `to_json()`: Serialize report
- `to_csv()`: Export errors to CSV format

---

## Relationships Diagram

```
WikiPage (1) ─────< (M) ImageAsset
    │
    │ (1)
    │
    ├─────< (M) LinkReference ────> (1) WikiPage (target)
    │
    │ (M)
    │
    └─────> (M) Category

ExportBundle contains:
    ├── Dict[WikiPage]
    ├── Dict[ImageAsset]
    └── List[LinkReference]

Checkpoint tracks:
    └── Set[page_id] (completed)

MigrationReport summarizes:
    └── List[error/warning] (issues)
```

---

## Storage Format

### On Disk (Export Output)

```
export_output/
├── Main/                          # Namespace directory
│   ├── Getting_Started.md         # Page as markdown
│   ├── Installation.md
│   └── images/                    # Images for this namespace
│       ├── GettingStarted-image-001.png
│       └── Installation-image-001.jpg
├── User/                          # Another namespace
│   ├── JohnDoe.md
│   └── images/
│       └── JohnDoe-image-001.png
├── .checkpoint                    # Checkpoint JSON file
├── export_metadata.json           # ExportBundle metadata
└── export_errors.csv              # Error log
```

### Checkpoint JSON Schema

```json
{
  "version": "1.0",
  "operation": "export",
  "timestamp": "2025-11-10T12:00:00Z",
  "pages_processed": 42,
  "images_processed": 156,
  "current_namespace": "Main",
  "current_page": "Getting Started",
  "completed_pages": ["1", "2", "3", ...],
  "config": {
    "source_url": "https://wiki.example.com",
    "link_depth": null,
    "target_namespaces": ["Main", "User"]
  }
}
```

---

## Type Hints (Python)

```python
from dataclasses import dataclass
from datetime import datetime
from typing import List, Dict, Set, Optional
from enum import Enum

class DownloadStatus(Enum):
    PENDING = "pending"
    DOWNLOADED = "downloaded"
    FAILED = "failed"
    UPLOADED = "uploaded"

class LinkType(Enum):
    INTERNAL = "internal"
    CATEGORY = "category"
    REDIRECT = "redirect"

@dataclass
class WikiPage:
    id: str
    title: str
    namespace: str
    content: str
    categories: List[str]
    links: List[str]
    images: List[str]
    url: str
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    author: Optional[str] = None
    revision_id: Optional[str] = None
    path: Optional[str] = None
    wikijs_id: Optional[str] = None

@dataclass
class ImageAsset:
    original_filename: str
    url: str
    page_references: List[str]
    download_status: DownloadStatus
    renamed_filename: Optional[str] = None
    local_path: Optional[str] = None
    content_type: Optional[str] = None
    size_bytes: Optional[int] = None
    error_message: Optional[str] = None
    wikijs_url: Optional[str] = None

@dataclass
class LinkReference:
    source_page: str
    target_page: str
    link_type: LinkType
    depth: int
    anchor_text: Optional[str] = None

@dataclass
class Checkpoint:
    version: str
    operation: str
    timestamp: datetime
    pages_processed: int
    images_processed: int
    completed_pages: Set[str]
    config: Dict
    current_namespace: Optional[str] = None
    current_page: Optional[str] = None
```

---

## Next Steps

- Define API contracts (contracts/)
- Create quickstart.md with usage examples
- Update agent context
