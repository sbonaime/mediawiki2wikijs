# MediaWiki to Wiki.js Migration Tool - Quickstart Guide

**Feature**: 001-mediawiki-wikijs-migration
**Version**: 1.0.0

## Overview

This tool migrates content from MediaWiki (version 1.13.5+) to Wiki.js (version 2.x), preserving page organization, links, images, and categories. The migration process consists of two separate scripts: **export** (from MediaWiki) and **import** (to Wiki.js).

---

## Prerequisites

### System Requirements

- **Python**: 3.9 or higher
- **Pandoc**: System-level installation required for wikitext → markdown conversion
- **Git**: For version control (optional but recommended)
- **Network**: HTTP/HTTPS access to both MediaWiki and Wiki.js instances

### Install Pandoc

**macOS** (via Homebrew):
```bash
brew install pandoc
```

**Linux** (Debian/Ubuntu):
```bash
sudo apt-get install pandoc
```

**Windows**:
Download installer from https://pandoc.org/installing.html

Verify installation:
```bash
pandoc --version
```

---

## Installation

### 1. Clone Repository

```bash
git clone <repository-url>
cd mediawiki2wikijs
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

**Dependencies installed**:
- `requests>=2.31.0` - HTTP client
- `mwclient>=0.10.0` - MediaWiki API wrapper
- `gql>=3.4.0` - Wiki.js GraphQL client
- `pypandoc>=1.11` - Pandoc wrapper
- `python-dotenv>=1.0.0` - Environment variable management

### 4. Verify Installation

```bash
python export_mediawiki.py --version
python import_wikijs.py --version
```

---

## Configuration

### Create `.env` File

Copy the template and fill in your credentials:

```bash
cp .env.example .env
```

**Edit `.env` with your settings**:

```ini
# MediaWiki Configuration
MEDIAWIKI_URL=https://wiki.example.com
MEDIAWIKI_USERNAME=BotUser
MEDIAWIKI_PASSWORD=BotPassword123

# Wiki.js Configuration
WIKIJS_URL=https://newwiki.example.com
WIKIJS_API_KEY=your-api-key-here

# Optional Settings
EXPORT_DIR=./export_data
CHECKPOINT_FREQUENCY=10
MAX_LINK_DEPTH=-1
LOG_LEVEL=INFO
```

### Configuration Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `MEDIAWIKI_URL` | MediaWiki instance URL (with http/https) | **Required** |
| `MEDIAWIKI_USERNAME` | Bot or admin username | **Required** |
| `MEDIAWIKI_PASSWORD` | User password | **Required** |
| `WIKIJS_URL` | Wiki.js instance URL (with https) | **Required** |
| `WIKIJS_API_KEY` | API key with `write:pages` and `write:assets` permissions | **Required** |
| `EXPORT_DIR` | Directory to store exported data | `./export_data` |
| `CHECKPOINT_FREQUENCY` | Save progress every N pages | `10` |
| `MAX_LINK_DEPTH` | Maximum link depth for crawling (-1 = unlimited) | `-1` |
| `LOG_LEVEL` | Logging verbosity (DEBUG, INFO, WARNING, ERROR) | `INFO` |

### Generate Wiki.js API Key

1. Log in to Wiki.js as administrator
2. Navigate to: **Administration** → **API Access**
3. Click **New API Key**
4. Set name: `MediaWiki Migration Bot`
5. Enable permissions: `write:pages`, `write:assets`
6. Copy generated key to `.env` file

---

## Basic Usage

### Step 1: Export from MediaWiki

Export all pages, images, and metadata from MediaWiki:

```bash
python export_mediawiki.py
```

**What happens**:
1. Authenticates with MediaWiki API
2. Lists all pages across namespaces
3. Downloads page content (wikitext)
4. Extracts links and categories
5. Downloads referenced images
6. Converts wikitext to markdown
7. Saves to local filesystem in `export_data/`
8. Creates checkpoint files for resume capability

**Output structure**:
```
export_data/
├── pages/
│   ├── Main/
│   │   ├── Getting_Started.md
│   │   └── Installation.md
│   └── User/
│       └── Admin.md
├── images/
│   ├── getting-started-logo.png
│   ├── installation-screenshot.jpg
│   └── admin-profile.png
├── export_metadata.json
├── export_errors.csv
└── .checkpoint
```

### Step 2: Import to Wiki.js

Import exported content to Wiki.js:

```bash
python import_wikijs.py --source ./export_data
```

**What happens**:
1. Authenticates with Wiki.js GraphQL API
2. Reads exported pages from `export_data/`
3. Creates pages with markdown content
4. Uploads images with renamed filenames
5. Preserves categories as tags
6. Updates internal links
7. Saves checkpoint files for resume capability

---

## Common Options

### Dry Run Mode

Preview migration without making changes:

```bash
# Export (test connection and list pages only)
python export_mediawiki.py --dry-run

# Import (validate data without creating pages)
python import_wikijs.py --source ./export_data --dry-run
```

### Limit Link Depth

Process only pages up to N links away from start page:

```bash
python export_mediawiki.py --link-depth 2
```

**Examples**:
- `--link-depth 0`: Only process start page
- `--link-depth 1`: Process start page + directly linked pages
- `--link-depth -1`: Process all linked pages (unlimited, default)

### Resume from Checkpoint

If migration is interrupted, resume from last checkpoint:

```bash
# Export (automatically detects .checkpoint file)
python export_mediawiki.py --resume

# Import (automatically detects .checkpoint file)
python import_wikijs.py --source ./export_data --resume
```

### Filter by Namespace

Export only specific MediaWiki namespaces:

```bash
# Main namespace only (0)
python export_mediawiki.py --namespaces 0

# Main and User namespaces (0, 2)
python export_mediawiki.py --namespaces 0,2
```

**Common namespace IDs**:
- `0`: Main (articles)
- `1`: Talk
- `2`: User
- `3`: User talk
- `4`: Project
- `6`: File
- `14`: Category

### Verbose Logging

Enable detailed debug output:

```bash
python export_mediawiki.py --verbose
python import_wikijs.py --source ./export_data --verbose
```

---

## Advanced Usage

### Custom Export Directory

Specify output location:

```bash
python export_mediawiki.py --output /path/to/export

# Import from custom location
python import_wikijs.py --source /path/to/export
```

### Skip Existing Pages

Skip pages that already exist in Wiki.js (no overwrite):

```bash
python import_wikijs.py --source ./export_data --skip-existing
```

### Force Overwrite

Overwrite existing pages in Wiki.js:

```bash
python import_wikijs.py --source ./export_data --force
```

### Export Single Page

Export only one page and its dependencies:

```bash
python export_mediawiki.py --start-page "Main Page"
```

### Custom Checkpoint Frequency

Save progress more/less frequently:

```bash
# Save every 5 pages (more frequent)
python export_mediawiki.py --checkpoint-frequency 5

# Save every 50 pages (less frequent)
python export_mediawiki.py --checkpoint-frequency 50
```

---

## Verification

### Check Migration Report

After import, review the generated report:

```bash
cat export_data/migration_report.json
```

**Report includes**:
- Total pages exported/imported
- Total images processed
- Success/failure counts
- List of errors and warnings
- Execution time

### Review Error Log

Check for pages that failed to migrate:

```bash
cat export_data/export_errors.csv
```

**CSV format**:
```csv
timestamp,page_id,page_title,error_type,error_message
2025-11-10T12:34:56,123,Corrupted Page,parse_error,Invalid wikitext syntax
```

### Verify Links

Test that internal links work correctly in Wiki.js:

1. Navigate to migrated pages in Wiki.js
2. Click internal links to ensure they resolve
3. Check that images display correctly

---

## Troubleshooting

### Authentication Timeout

**Problem**: `Authentication failed: Session expired`

**Solution**: Increase inactivity timeout threshold in `.env`:
```ini
AUTH_TIMEOUT_SECONDS=600  # 10 minutes instead of 5
```

### Pandoc Not Found

**Problem**: `FileNotFoundError: pandoc executable not found`

**Solution**: Install Pandoc system-wide (see Prerequisites section)

### Image Download Failures

**Problem**: Some images fail to download

**Solution**: Check image URLs are accessible:
```bash
curl -I https://wiki.example.com/images/a/ab/Logo.png
```

If 403 Forbidden, bot user may need `read` permissions on File namespace.

### API Rate Limiting

**Problem**: `HTTP 429: Too Many Requests`

**Solution**: Reduce request rate by adding delays:
```bash
python export_mediawiki.py --delay 1.0  # 1 second delay between requests
```

### Page Already Exists

**Problem**: Import fails with "Page already exists at this path"

**Solution**: Use `--skip-existing` flag or `--force` to overwrite:
```bash
python import_wikijs.py --source ./export_data --skip-existing
```

### Link Conversion Errors

**Problem**: Some MediaWiki links don't convert properly

**Solution**: Review `export_errors.csv` for patterns; may require manual fixes post-migration

### Checkpoint Corruption

**Problem**: Cannot resume from checkpoint

**Solution**: Delete `.checkpoint` file and restart:
```bash
rm export_data/.checkpoint
python export_mediawiki.py
```

---

## Performance Tips

### Large Wikis (>1000 pages)

- Use `--checkpoint-frequency 10` to save progress frequently
- Enable `--verbose` to monitor progress
- Run export overnight for very large wikis
- Consider filtering by namespace to migrate in batches

### Slow Network Connections

- Increase timeout thresholds: `--timeout 60` (60 seconds)
- Process fewer pages per batch: `--batch-size 10`

### Memory Constraints

- Export and import in separate sessions (don't run simultaneously)
- Clear export data after successful import: `rm -rf export_data/`

---

## Complete Example Workflow

### 1. Initial Setup

```bash
# Install dependencies
brew install pandoc  # macOS
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Configure credentials
cp .env.example .env
nano .env  # Fill in MEDIAWIKI_URL, credentials, WIKIJS_API_KEY
```

### 2. Test Connections (Dry Run)

```bash
# Test MediaWiki connection
python export_mediawiki.py --dry-run

# Test Wiki.js connection
python import_wikijs.py --source ./export_data --dry-run
```

### 3. Export Main Namespace

```bash
# Export only main articles
python export_mediawiki.py --namespaces 0 --verbose
```

### 4. Review Export

```bash
# Check exported files
ls -lR export_data/pages/
cat export_data/export_metadata.json

# Review errors
cat export_data/export_errors.csv
```

### 5. Import to Wiki.js

```bash
# Import with skip-existing safety
python import_wikijs.py --source ./export_data --skip-existing --verbose
```

### 6. Verify Migration

```bash
# Check migration report
cat export_data/migration_report.json

# Manually verify links in Wiki.js UI
```

---

## Next Steps

- **Customize Templates**: Edit `lib/converters/wikitext_to_markdown.py` to adjust conversion rules
- **Add Custom Categories**: Map MediaWiki categories to Wiki.js tags in `lib/mappers/category_mapper.py`
- **Automate**: Schedule periodic exports using cron or systemd timers
- **CI/CD Integration**: See `docs/ci-cd-integration.md` for GitHub Actions examples

---

## Support

- **Documentation**: See `docs/` directory for detailed guides
- **API References**: Review `specs/001-mediawiki-wikijs-migration/contracts/` for API details
- **Report Issues**: Create GitHub issue with error logs and `export_metadata.json`
- **Community**: Join Wiki.js Discord for migration tips

---

## Changelog

### v1.0.0 (2025-11-10)
- Initial release
- MediaWiki 1.13.5+ support
- Wiki.js 2.x GraphQL API integration
- Checkpoint/resume functionality
- Dry-run mode
- Image renaming based on page slug
