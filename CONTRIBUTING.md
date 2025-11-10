# Contributing to MediaWiki to Wiki.js Migration Tool

Thank you for your interest in contributing! This document provides guidelines and instructions for contributing to the project.

## 🎯 Project Overview

This tool migrates MediaWiki sites to Wiki.js, preserving content, structure, and relationships. The project is structured in phases (see [tasks.md](specs/001-mediawiki-wikijs-migration/tasks.md)):

- **Phases 1-5**: ✅ Complete (MVP functional)
- **Phase 6**: ⏳ Verification tools (in progress)
- **Phase 7**: ⏳ Testing and polish (planned)

## 🚀 Getting Started

### Prerequisites

- Python 3.9+ (3.11+ recommended)
- Pandoc (system installation required)
- Git
- MediaWiki instance for testing (optional)
- Wiki.js instance for testing (optional)

### Development Setup

1. **Fork and clone**:
   ```bash
   git clone https://github.com/sbonaime/mediawiki2wikijs.git
   cd mediawiki2wikijs
   ```

2. **Create virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up test environment**:
   ```bash
   cp .env.example .env
   # Edit .env with test MediaWiki/Wiki.js credentials
   ```

## 📝 Code Style

### Python Style Guide

- Follow [PEP 8](https://pep8.org/) style guidelines
- Use type hints for all function signatures
- Add docstrings for all modules, classes, and functions (Google style)
- Keep functions focused and under 50 lines when possible
- Use dataclasses for data models

### Example Code Style

```python
"""Module docstring explaining purpose."""

from typing import List, Optional
from dataclasses import dataclass


@dataclass
class Example:
    """Class docstring.

    Attributes:
        name: Description of name field
        value: Description of value field
    """
    name: str
    value: int

    def process(self) -> bool:
        """Process the example.

        Returns:
            True if processing succeeds, False otherwise
        """
        # Implementation
        return True


def transform_content(content: str, options: Optional[dict] = None) -> str:
    """Transform content using specified options.

    Args:
        content: Input content to transform
        options: Optional transformation settings

    Returns:
        Transformed content

    Raises:
        ValueError: If content is empty
    """
    if not content:
        raise ValueError("Content cannot be empty")

    # Implementation
    return content
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest tests/

# Run specific test file
pytest tests/unit/test_content_transformer.py

# Run with coverage
pytest --cov=src tests/
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use descriptive test names: `test_transform_converts_wikitext_to_markdown`
- Test both success and error cases
- Use fixtures for common setup

Example test:

```python
import pytest
from src.lib.content_transformer import ContentTransformer


def test_normalize_page_title_creates_url_safe_path():
    """Test that page titles are converted to URL-safe paths."""
    transformer = ContentTransformer()

    result = transformer.normalize_page_title("Getting Started Guide")

    assert result == "getting-started-guide"


def test_normalize_page_title_handles_special_characters():
    """Test special character handling in page titles."""
    transformer = ContentTransformer()

    result = transformer.normalize_page_title("User:Admin/Notes (2023)")

    assert result == "user-admin-notes-2023"
```

## 🔀 Branching Strategy

### Branch Naming

- `feature/description` - New features
- `fix/description` - Bug fixes
- `docs/description` - Documentation updates
- `refactor/description` - Code refactoring
- `test/description` - Test additions

### Workflow

1. **Create feature branch** from `main`:
   ```bash
   git checkout -b feature/my-new-feature
   ```

2. **Make changes** with atomic commits:
   ```bash
   git add src/lib/new_module.py
   git commit -m "Add new module for feature X"
   ```

3. **Keep branch updated**:
   ```bash
   git fetch origin
   git rebase origin/main
   ```

4. **Push and create PR**:
   ```bash
   git push origin feature/my-new-feature
   ```

## 📋 Commit Guidelines

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes (formatting, no logic change)
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples

```
feat(transformer): Add image reference updating

Implement update_image_references method to convert MediaWiki
image syntax to markdown format and update filenames based on
the image_mapping dictionary.

Closes #42
```

```
fix(auth): Handle session timeout during long exports

Add timeout detection in auth_manager to automatically
reconnect when 5-minute inactivity threshold is exceeded.

Fixes #38
```

## 🐛 Reporting Issues

### Bug Reports

Include:
- **Description**: What went wrong?
- **Steps to Reproduce**: Numbered list of steps
- **Expected Behavior**: What should have happened?
- **Actual Behavior**: What actually happened?
- **Environment**:
  - OS (macOS, Linux, Windows)
  - Python version
  - Pandoc version
- **Logs**: Relevant error messages
- **Files**: `export_metadata.json`, `export_errors.csv` if applicable

### Feature Requests

Include:
- **Description**: What feature do you want?
- **Use Case**: Why is this feature needed?
- **Proposed Solution**: How should it work?
- **Alternatives**: Other approaches you've considered

## 📚 Documentation

### Documentation Updates

- Update relevant `.md` files in `specs/001-mediawiki-wikijs-migration/`
- Add docstrings to new code
- Update README.md if user-facing changes
- Update quickstart.md for usage changes

### Documentation Structure

```
specs/001-mediawiki-wikijs-migration/
├── spec.md           # Feature specification
├── plan.md           # Implementation plan
├── tasks.md          # Task breakdown
├── research.md       # Technical decisions
├── data-model.md     # Data models
├── quickstart.md     # User guide
└── contracts/        # API documentation
```

## 🎁 Pull Request Process

1. **Ensure tests pass**: Run `pytest tests/`
2. **Update documentation**: Add/update relevant docs
3. **Add tests**: Cover new functionality
4. **Run linting**: `ruff check src/`
5. **Update CHANGELOG**: Add entry for your changes (if applicable)
6. **Create PR**: Use template and reference issues
7. **Wait for review**: Address feedback promptly

### PR Checklist

- [ ] Code follows project style guidelines
- [ ] Tests added/updated and passing
- [ ] Documentation updated
- [ ] No breaking changes (or documented if necessary)
- [ ] Commit messages follow guidelines
- [ ] Branch is up to date with main

## 🏗️ Architecture Guidelines

### Project Structure

```
src/
├── export.py              # Export CLI (entry point)
├── import_wikijs.py       # Import CLI (entry point)
├── lib/                   # Shared libraries
│   ├── config.py          # Configuration
│   ├── logger.py          # Logging
│   ├── *_client.py        # API clients
│   ├── *_processor.py     # Processors
│   └── *_manager.py       # Managers
└── models/                # Data models
    └── *.py               # Dataclass models
```

### Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Dependency Injection**: Pass dependencies explicitly
3. **Error Handling**: Use try-except with specific exceptions
4. **Logging**: Log at appropriate levels (DEBUG, INFO, WARNING, ERROR)
5. **Type Safety**: Use type hints throughout
6. **Testability**: Write code that's easy to test

## 🌟 Areas for Contribution

### High Priority

- [ ] **Phase 6: Verification tools** (T064-T072)
- [ ] **Error recovery improvements**
- [ ] **Performance optimizations**
- [ ] **Test coverage increase**

### Medium Priority

- [ ] **Phase 7: Polish** (T073-T090)
- [ ] **CI/CD setup** (GitHub Actions)
- [ ] **Docker support**
- [ ] **Additional MediaWiki versions**

### Low Priority

- [ ] **GUI interface**
- [ ] **Progress bar enhancements**
- [ ] **Additional output formats**

See [tasks.md](specs/001-mediawiki-wikijs-migration/tasks.md) for detailed task breakdown.

## 💬 Communication

- **GitHub Issues**: Bug reports and feature requests
- **Pull Requests**: Code contributions and discussions
- **Discussions**: General questions and ideas

## 📄 License

By contributing, you agree that your contributions will be licensed under the MIT License.

## 🙏 Recognition

Contributors will be acknowledged in:
- README.md contributors section
- Release notes
- GitHub contributor graph

Thank you for making this project better! 🎉
