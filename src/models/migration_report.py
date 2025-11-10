"""MigrationReport model for MediaWiki to Wiki.js migration tool.

This module defines the MigrationReport dataclass for summarizing
migration activities and results.
"""

import json
import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


@dataclass
class MigrationReport:
    """Summary of migration activities and results.

    Attributes:
        operation: "export", "import", or "verification"
        start_time: Operation start timestamp
        status: "in_progress", "completed", "failed"
        pages_total: Total pages to process
        pages_succeeded: Pages successfully processed
        pages_failed: Pages that encountered errors
        pages_skipped: Pages skipped (e.g., already exist in Wiki.js)
        images_total: Total images to process
        images_succeeded: Images successfully processed
        images_failed: Images that encountered errors
        errors: List of error records with page/image details
        warnings: List of warnings (e.g., skipped pages)
        end_time: Operation completion timestamp
    """

    operation: str
    start_time: datetime
    status: str
    pages_total: int = 0
    pages_succeeded: int = 0
    pages_failed: int = 0
    pages_skipped: int = 0
    images_total: int = 0
    images_succeeded: int = 0
    images_failed: int = 0
    errors: List[Dict] = field(default_factory=list)
    warnings: List[Dict] = field(default_factory=list)
    end_time: Optional[datetime] = None

    def __post_init__(self):
        """Validate required fields."""
        if self.operation not in ("export", "import", "verification"):
            raise ValueError("Operation must be 'export', 'import', or 'verification'")
        if self.status not in ("in_progress", "completed", "failed"):
            raise ValueError("Status must be 'in_progress', 'completed', or 'failed'")

    def add_error(self, page_id: str, page_title: str, error_type: str, error_message: str):
        """Record an error.

        Args:
            page_id: Page ID that encountered error
            page_title: Page title for reference
            error_type: Type of error (e.g., "parse_error", "network_error")
            error_message: Detailed error message
        """
        self.errors.append({
            "timestamp": datetime.now().isoformat(),
            "page_id": page_id,
            "page_title": page_title,
            "error_type": error_type,
            "error_message": error_message
        })
        self.pages_failed += 1

    def add_warning(self, page_id: str, page_title: str, warning_type: str, warning_message: str):
        """Record a warning.

        Args:
            page_id: Page ID that generated warning
            page_title: Page title for reference
            warning_type: Type of warning (e.g., "already_exists", "skipped")
            warning_message: Detailed warning message
        """
        self.warnings.append({
            "timestamp": datetime.now().isoformat(),
            "page_id": page_id,
            "page_title": page_title,
            "warning_type": warning_type,
            "warning_message": warning_message
        })

    def mark_page_succeeded(self):
        """Increment the count of successfully processed pages."""
        self.pages_succeeded += 1

    def mark_page_skipped(self):
        """Increment the count of skipped pages."""
        self.pages_skipped += 1

    def mark_image_succeeded(self):
        """Increment the count of successfully processed images."""
        self.images_succeeded += 1

    def mark_image_failed(self):
        """Increment the count of failed images."""
        self.images_failed += 1

    def complete(self):
        """Mark the operation as completed."""
        self.status = "completed"
        self.end_time = datetime.now()

    def fail(self):
        """Mark the operation as failed."""
        self.status = "failed"
        self.end_time = datetime.now()

    def duration_seconds(self) -> Optional[float]:
        """Calculate operation duration in seconds.

        Returns:
            Duration in seconds, or None if operation not finished
        """
        if self.end_time is None:
            return None
        return (self.end_time - self.start_time).total_seconds()

    def to_json(self, filepath: str):
        """Serialize report to JSON file.

        Args:
            filepath: Path to save report (e.g., "migration_report.json")
        """
        report_data = {
            "operation": self.operation,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "duration_seconds": self.duration_seconds(),
            "status": self.status,
            "pages": {
                "total": self.pages_total,
                "succeeded": self.pages_succeeded,
                "failed": self.pages_failed,
                "skipped": self.pages_skipped
            },
            "images": {
                "total": self.images_total,
                "succeeded": self.images_succeeded,
                "failed": self.images_failed
            },
            "errors": self.errors,
            "warnings": self.warnings
        }

        filepath_obj = Path(filepath)
        filepath_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)

    def to_csv(self, filepath: str):
        """Export errors to CSV format.

        Args:
            filepath: Path to save CSV (e.g., "export_errors.csv")
        """
        if not self.errors:
            return  # No errors to write

        filepath_obj = Path(filepath)
        filepath_obj.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['timestamp', 'page_id', 'page_title', 'error_type', 'error_message'])
            writer.writeheader()
            writer.writerows(self.errors)

    def summary(self) -> str:
        """Generate a human-readable summary.

        Returns:
            Formatted summary string
        """
        lines = [
            f"Operation: {self.operation}",
            f"Status: {self.status}",
            f"Duration: {self.duration_seconds():.2f}s" if self.duration_seconds() else "Duration: In progress",
            "",
            f"Pages: {self.pages_succeeded}/{self.pages_total} succeeded, {self.pages_failed} failed, {self.pages_skipped} skipped",
            f"Images: {self.images_succeeded}/{self.images_total} succeeded, {self.images_failed} failed",
            "",
            f"Errors: {len(self.errors)}",
            f"Warnings: {len(self.warnings)}"
        ]
        return "\n".join(lines)
