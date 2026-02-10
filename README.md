# MediaWiki to Wiki.js Migration Tool

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Pandoc Required](https://img.shields.io/badge/requires-pandoc-orange.svg)](https://pandoc.org/)

A comprehensive Python-based tool for migrating complete MediaWiki sites to Wiki.js, preserving page organization, internal links, images, and categories. Designed for reliability with checkpoint/resume functionality and automatic authentication management.

## ✨ Features

- **Complete Export**: Extract all pages, images, and metadata from MediaWiki (v1.13.5+)
- **Content Transformation**: Convert wikitext to markdown with automatic link and image reference updates
- **Intelligent Import**: Create pages and upload images to Wiki.js via GraphQL API
- **Resumable Operations**: Checkpoint every 10 pages for large wiki migrations
- **Flexible Authentication**: Supports both public wikis (anonymous access) and private wikis (automatic reconnection on timeout)
- **Dry-Run Mode**: Preview operations without making changes
- **Link Depth Control**: Configurable BFS traversal for selective export
- **Error Recovery**: Comprehensive logging with CSV error reports

## Requirements

- **Python**: 3.9 or higher (3.11+ recommended for performance)
- **Pandoc**: System-level installation required for wikitext→markdown conversion
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

**Windows**: Download from https://pandoc.org/installing.html

## 📋 Table of Contents

- [Requirements](#requirements)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Documentation](#documentation)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/sbonaime/mediawiki2wikijs.git
   cd mediawiki2wikijs
   ```

2. **Install dependencies with uv**:
   ```bash
   uv sync
   ```

3. **Configure settings**:
   ```bash
   cp .env.example .env
   # Edit .env with your MediaWiki URL and Wiki.js credentials
   # Note: MediaWiki username/password are optional (leave empty for public wikis)
   ```

## Quick Start

### 1. Export from MediaWiki

```bash
uv run python src/export_mediawiki.py
```

This will:
- Connect to your MediaWiki instance
- Export all pages to `export_output/` directory
- Download all images
- Convert content to markdown
- Save checkpoint every 10 pages

### 2. Import to Wiki.js

```bash
uv run python src/import_wikijs.py --source ./export_output
```

This will:
- Connect to your Wiki.js instance
- Create all pages with markdown content
- Upload all images
- Update internal links

## Configuration

### Environment Variables

Edit your `.env` file with these settings:

```bash
# MediaWiki Configuration
MEDIAWIKI_URL=https://wiki.example.com

# Optional: For private wikis that require authentication
# Leave empty for public wikis
MEDIAWIKI_USERNAME=YourUsername
MEDIAWIKI_PASSWORD=YourPassword

# Wiki.js Configuration (required)
WIKIJS_URL=https://newwiki.example.com
WIKIJS_API_KEY=your-api-key-here

# Optional Settings
EXPORT_DIR=./export_output
CHECKPOINT_FREQUENCY=10
MAX_LINK_DEPTH=-1
LOG_LEVEL=INFO
```

**Public vs Private Wikis:**
- **Public wikis**: Leave `MEDIAWIKI_USERNAME` and `MEDIAWIKI_PASSWORD` empty or remove them. The tool will connect anonymously.
- **Private wikis**: Provide valid credentials. The tool will automatically handle authentication and reconnection on timeout.

## Usage Examples

### Export Options

```bash
# Dry run (preview without downloading)
uv run python src/export_mediawiki.py --dry-run

# Limit link depth
uv run python src/export_mediawiki.py --link-depth 2

# Resume interrupted export
uv run python src/export_mediawiki.py --resume

# Export specific namespaces
uv run python src/export_mediawiki.py --namespaces 0,2

# Verbose logging
uv run python src/export_mediawiki.py --verbose
```

### Import Options

```bash
# Dry run (preview without creating pages)
uv run python src/import_wikijs.py --source ./export_output --dry-run

# Skip existing pages
uv run python src/import_wikijs.py --source ./export_output --skip-existing

# Force overwrite existing pages
uv run python src/import_wikijs.py --source ./export_output --force

# Resume interrupted import
uv run python src/import_wikijs.py --source ./export_output --resume
```

## Documentation

- **[Quickstart Guide](specs/001-mediawiki-wikijs-migration/quickstart.md)**: Detailed installation and usage instructions
- **[Feature Specification](specs/001-mediawiki-wikijs-migration/spec.md)**: Complete feature requirements
- **[Implementation Plan](specs/001-mediawiki-wikijs-migration/plan.md)**: Technical architecture and design
- **[API Contracts](specs/001-mediawiki-wikijs-migration/contracts/)**: MediaWiki and Wiki.js API documentation

## Project Structure

```
src/
├── export_mediawiki.py        # Export CLI script
├── import_wikijs.py           # Import CLI script
├── lib/                       # Shared library code
│   ├── config.py              # Configuration management
│   ├── logger.py              # Logging utilities
│   ├── mediawiki_client.py    # MediaWiki API client
│   ├── wikijs_client.py       # Wiki.js GraphQL client
│   ├── content_transformer.py # Markup conversion
│   ├── storage_manager.py     # File system operations
│   ├── image_processor.py     # Image handling
│   └── auth_manager.py        # Authentication management
└── models/                    # Data models
    ├── wiki_page.py           # Page entity
    ├── image_asset.py         # Image entity
    ├── link_reference.py      # Link relationship
    ├── checkpoint.py          # Checkpoint state
    └── migration_report.py    # Migration report

tests/
├── unit/                      # Unit tests
├── integration/               # Integration tests
└── contract/                  # API contract tests
```

## Troubleshooting

### Authentication Timeout
If you see "Authentication failed: Session expired", the script will automatically reconnect after 5 minutes of inactivity.

### Pandoc Not Found
Install Pandoc system-wide (see Requirements section above).

### Image Download Failures
Check that your MediaWiki bot user has `read` permissions on the File namespace.

### Page Already Exists
Use `--skip-existing` flag to skip existing pages, or `--force` to overwrite.

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Make your changes**: Follow existing code style and add tests
4. **Commit**: `git commit -m 'Add amazing feature'`
5. **Push**: `git push origin feature/amazing-feature`
6. **Open a Pull Request**

See [tasks.md](specs/001-mediawiki-wikijs-migration/tasks.md) for planned features and open tasks.

### Development Setup

```bash
# Install development dependencies
uv sync

# Run tests
uv run pytest tests/

# Run linting
uv run ruff check src/
```

## � Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes and releases.

## �📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For issues and questions:
- 📖 Review the [Quickstart Guide](specs/001-mediawiki-wikijs-migration/quickstart.md)
- 🔧 Check the [Troubleshooting section](specs/001-mediawiki-wikijs-migration/quickstart.md#troubleshooting)
- 🐛 Create a [GitHub issue](https://github.com/sbonaime/mediawiki2wikijs/issues) with error logs and `export_metadata.json`

## 🙏 Acknowledgments

- **MediaWiki API**: Powered by [mwclient](https://github.com/mwclient/mwclient)
- **Wiki.js GraphQL**: Using [gql](https://github.com/graphql-python/gql)
- **Pandoc**: Universal document converter by John MacFarlane

## 📊 Status

**Project Status**: ✅ **MVP Complete** (70% of planned features implemented)

- ✅ Phase 1-2: Setup and foundational infrastructure
- ✅ Phase 3: MediaWiki export with BFS traversal
- ✅ Phase 4: Content transformation (wikitext→markdown)
- ✅ Phase 5: Wiki.js import with GraphQL
- ⏳ Phase 6: Verification tools (planned)
- ⏳ Phase 7: Testing and polish (planned)

See [tasks.md](specs/001-mediawiki-wikijs-migration/tasks.md) for detailed progress tracking.
