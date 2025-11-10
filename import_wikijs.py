#!/usr/bin/env python3
"""Import command-line interface for MediaWiki to Wiki.js migration tool.

This script imports transformed content into Wiki.js, including pages and images.
Supports resumable operations via checkpoints, dry-run mode, and collision handling.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional, Dict

from src.lib.config import load_config
from src.lib.logger import setup_logger, CSVErrorLogger
from src.lib.storage_manager import StorageManager
from src.lib.wikijs_client import WikiJsClient
from src.models import WikiPage, ImageAsset, Checkpoint, MigrationReport


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Import content to Wiki.js from MediaWiki export',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Import with default settings (from .env)
  python import_wikijs.py

  # Import from custom export directory
  python import_wikijs.py --source /path/to/export

  # Dry-run to see what would be imported
  python import_wikijs.py --dry-run

  # Skip existing pages (don't update)
  python import_wikijs.py --skip-existing

  # Force update existing pages
  python import_wikijs.py --force

  # Resume from checkpoint
  python import_wikijs.py --resume

  # Verbose logging
  python import_wikijs.py --verbose
        """
    )

    # Source options
    parser.add_argument(
        '--source',
        type=str,
        help='Export source directory (overrides .env EXPORT_DIR)'
    )

    # Collision handling
    collision_group = parser.add_mutually_exclusive_group()
    collision_group.add_argument(
        '--skip-existing',
        action='store_true',
        help='Skip pages that already exist (default behavior)'
    )
    collision_group.add_argument(
        '--force',
        action='store_true',
        help='Update existing pages instead of skipping'
    )

    # Checkpoint options
    parser.add_argument(
        '--resume',
        action='store_true',
        help='Resume from last checkpoint'
    )
    parser.add_argument(
        '--checkpoint-frequency',
        type=int,
        help='Save checkpoint every N pages (overrides .env)'
    )

    # Operational options
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be imported without making changes'
    )
    parser.add_argument(
        '--skip-images',
        action='store_true',
        help='Skip image uploads'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of pages to import'
    )

    # Logging options
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging (DEBUG level)'
    )
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (overrides .env)'
    )

    return parser.parse_args()


def load_page_from_file(file_path: Path, logger) -> Optional[WikiPage]:
    """Load a WikiPage from a markdown file.

    Args:
        file_path: Path to markdown file
        logger: Logger instance

    Returns:
        WikiPage object or None if loading fails
    """
    try:
        # Read markdown content
        content = file_path.read_text(encoding='utf-8')

        # Extract metadata from filename/path
        title = file_path.stem  # Remove .md extension
        namespace = file_path.parent.name

        # Create WikiPage object
        page = WikiPage(
            id=str(hash(str(file_path))),  # Generate ID from path
            title=title,
            namespace=namespace,
            content=content
        )

        return page

    except Exception as e:
        logger.error(f"Error loading page from '{file_path}': {e}")
        return None


def import_page(
    client: WikiJsClient,
    page: WikiPage,
    force: bool,
    dry_run: bool,
    logger
) -> tuple[bool, str]:
    """Import a single page to Wiki.js.

    Args:
        client: Wiki.js API client
        page: WikiPage object to import
        force: Whether to update existing pages
        dry_run: Whether this is a dry-run
        logger: Logger instance

    Returns:
        Tuple of (success: bool, status: str)
        Status can be: 'created', 'updated', 'skipped', 'failed'
    """
    try:
        # Generate path from title if not set
        if not page.path:
            from src.lib.content_transformer import ContentTransformer
            transformer = ContentTransformer()
            page.path = transformer.normalize_page_title(page.title)

        if dry_run:
            logger.info(f"[DRY-RUN] Would import: {page.title} at /{page.path}")
            return True, 'dry-run'

        # Check if page already exists
        existing = client.get_page_by_path(page.path)

        if existing:
            if force:
                # Update existing page
                logger.info(f"Updating existing page: {page.title}")
                result = client.update_page(
                    page_id=existing['id'],
                    content=page.content,
                    description=f"Migrated from MediaWiki: {page.title}",
                    path=page.path,
                    title=page.title,
                    tags=page.categories or []
                )

                if result['responseResult']['succeeded']:
                    logger.info(f"Successfully updated: {page.title}")
                    return True, 'updated'
                else:
                    error_msg = result['responseResult'].get('message', 'Unknown error')
                    logger.error(f"Failed to update '{page.title}': {error_msg}")
                    return False, 'failed'
            else:
                # Skip existing page
                logger.info(f"Skipping existing page: {page.title}")
                return True, 'skipped'
        else:
            # Create new page
            logger.info(f"Creating new page: {page.title}")
            result = client.create_page(
                content=page.content,
                description=f"Migrated from MediaWiki: {page.title}",
                path=page.path,
                title=page.title,
                tags=page.categories or []
            )

            if result['responseResult']['succeeded']:
                logger.info(f"Successfully created: {page.title}")

                # Store Wiki.js page ID
                if 'page' in result and result['page']:
                    page.wikijs_id = str(result['page']['id'])

                return True, 'created'
            else:
                error_code = result['responseResult'].get('errorCode', 0)
                error_msg = result['responseResult'].get('message', 'Unknown error')

                # Check for collision error (error code 1001)
                if error_code == 1001:
                    logger.warning(f"Page collision for '{page.title}': {error_msg}")
                    return True, 'skipped'
                else:
                    logger.error(f"Failed to create '{page.title}': {error_msg}")
                    return False, 'failed'

    except Exception as e:
        logger.error(f"Error importing page '{page.title}': {e}")
        return False, 'failed'


def import_image(
    client: WikiJsClient,
    image_path: Path,
    folder_id: Optional[int],
    dry_run: bool,
    logger
) -> bool:
    """Import a single image to Wiki.js.

    Args:
        client: Wiki.js API client
        image_path: Path to image file
        folder_id: Target folder ID (optional)
        dry_run: Whether this is a dry-run
        logger: Logger instance

    Returns:
        True if import succeeds, False otherwise
    """
    try:
        if dry_run:
            logger.info(f"[DRY-RUN] Would upload: {image_path.name}")
            return True

        logger.debug(f"Uploading image: {image_path.name}")

        result = client.upload_asset(
            file_path=str(image_path),
            folder_id=folder_id
        )

        if result.get('ok'):
            logger.debug(f"Successfully uploaded: {image_path.name}")
            return True
        else:
            error_msg = result.get('error', 'Unknown error')
            logger.warning(f"Failed to upload '{image_path.name}': {error_msg}")
            return False

    except Exception as e:
        logger.error(f"Error uploading image '{image_path.name}': {e}")
        return False


def main():
    """Main import function."""
    # Parse arguments
    args = parse_arguments()

    # Load configuration
    config = load_config()

    # Override config with command-line arguments
    if args.source:
        config.export_dir = Path(args.source)
    if args.checkpoint_frequency:
        config.checkpoint_frequency = args.checkpoint_frequency
    if args.log_level:
        config.log_level = args.log_level
    elif args.verbose:
        config.log_level = 'DEBUG'

    # Setup logging
    logger = setup_logger('import', level=config.log_level)
    logger.info("=" * 80)
    logger.info("Wiki.js Import Tool")
    logger.info("=" * 80)

    if args.dry_run:
        logger.info("DRY-RUN MODE: No changes will be made")

    # Validate export directory
    if not config.export_dir.exists():
        logger.error(f"Export directory not found: {config.export_dir}")
        sys.exit(1)

    # Initialize components
    storage = StorageManager(config.export_dir)
    error_logger = CSVErrorLogger(config.export_dir / 'import_errors.csv')

    # Initialize Wiki.js client
    logger.info("Connecting to Wiki.js...")
    client = WikiJsClient(
        url=config.wikijs_url,
        api_key=config.wikijs_api_key
    )

    # Load or create checkpoint
    checkpoint: Optional[Checkpoint] = None
    if args.resume:
        checkpoint = storage.load_checkpoint()
        if checkpoint:
            logger.info(f"Resuming from checkpoint: {checkpoint.pages_processed} pages processed")
        else:
            logger.warning("No checkpoint found, starting fresh import")
            checkpoint = Checkpoint.create_new()
    else:
        checkpoint = Checkpoint.create_new()

    # Get pages to import
    page_files = storage.list_pages()

    if not page_files:
        logger.warning("No pages found to import")
        sys.exit(0)

    logger.info(f"Found {len(page_files)} pages in export directory")

    # Filter already processed pages if resuming
    if args.resume and checkpoint:
        original_count = len(page_files)
        page_files = [
            p for p in page_files
            if not checkpoint.should_skip(str(hash(str(p))))
        ]
        skipped = original_count - len(page_files)
        if skipped > 0:
            logger.info(f"Skipping {skipped} already processed pages")

    # Apply limit if specified
    if args.limit and len(page_files) > args.limit:
        page_files = page_files[:args.limit]
        logger.info(f"Limited to {args.limit} pages")

    # Initialize migration report
    report = MigrationReport.create()

    # Import each page
    logger.info(f"Importing {len(page_files)} pages...")
    logger.info("")

    pages_created = 0
    pages_updated = 0
    pages_skipped = 0
    pages_failed = 0

    try:
        for idx, page_file in enumerate(page_files, start=1):
            logger.info(f"[{idx}/{len(page_files)}] Processing: {page_file.name}")

            # Load page from file
            page = load_page_from_file(page_file, logger)

            if not page:
                pages_failed += 1
                report.add_error(str(page_file), 'load_failed', 'Failed to load page from file')
                continue

            # Import page
            success, status = import_page(
                client=client,
                page=page,
                force=args.force,
                dry_run=args.dry_run,
                logger=logger
            )

            if success:
                if status == 'created':
                    pages_created += 1
                elif status == 'updated':
                    pages_updated += 1
                elif status == 'skipped':
                    pages_skipped += 1

                checkpoint.mark_page_processed(page.id, page.title)
            else:
                pages_failed += 1
                report.add_error(page.title, 'import_failed', f'Failed to import page (status: {status})')

            # Save checkpoint periodically
            if not args.dry_run and idx % config.checkpoint_frequency == 0:
                storage.save_checkpoint(checkpoint)
                logger.info(f"Checkpoint saved ({checkpoint.pages_processed} pages)")

            logger.info("")

    except KeyboardInterrupt:
        logger.warning("Import interrupted by user")
        if not args.dry_run:
            storage.save_checkpoint(checkpoint)
            logger.info("Checkpoint saved")
        sys.exit(130)

    # Import images if not skipped
    if not args.skip_images:
        logger.info("")
        logger.info("=" * 80)
        logger.info("IMPORTING IMAGES")
        logger.info("=" * 80)

        image_files = storage.list_images()
        logger.info(f"Found {len(image_files)} images to upload")

        # Get asset folders (optional)
        folder_id = None
        try:
            folders = client.get_asset_folders()
            if folders:
                logger.info(f"Found {len(folders)} asset folders")
        except Exception as e:
            logger.warning(f"Could not retrieve asset folders: {e}")

        images_success = 0
        images_failed = 0

        for idx, image_file in enumerate(image_files, start=1):
            logger.info(f"[{idx}/{len(image_files)}] Uploading: {image_file.name}")

            if import_image(client, image_file, folder_id, args.dry_run, logger):
                images_success += 1
            else:
                images_failed += 1
                error_logger.log_image_error(
                    str(image_file),
                    'upload_failed',
                    'Failed to upload image'
                )

        report.images_uploaded_success = images_success
        report.images_uploaded_failed = images_failed

    # Complete report
    report.pages_imported_success = pages_created + pages_updated
    report.pages_imported_failed = pages_failed
    report.complete()

    # Final checkpoint save
    if not args.dry_run:
        storage.save_checkpoint(checkpoint)
        logger.info("Final checkpoint saved")

    # Delete checkpoint if import is complete
    if not args.dry_run and pages_failed == 0:
        storage.delete_checkpoint()
        logger.info("Import complete, checkpoint deleted")

    # Print summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("IMPORT SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Pages created: {pages_created}")
    logger.info(f"Pages updated: {pages_updated}")
    logger.info(f"Pages skipped: {pages_skipped}")
    logger.info(f"Pages failed: {pages_failed}")

    if not args.skip_images:
        logger.info(f"Images uploaded: {report.images_uploaded_success}")
        logger.info(f"Images failed: {report.images_uploaded_failed}")

    logger.info(f"Duration: {report.duration_seconds():.1f} seconds")

    if report.errors:
        logger.warning(f"Errors encountered: {len(report.errors)}")
        logger.info(f"See {config.export_dir / 'import_errors.csv'} for details")

    # Save report
    if not args.dry_run:
        report_path = config.export_dir / 'import_report.json'
        with open(report_path, 'w') as f:
            f.write(report.to_json())
        logger.info(f"Report saved to: {report_path}")

    logger.info("=" * 80)

    # Exit with appropriate code
    if pages_failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
