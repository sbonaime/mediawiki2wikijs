#!/usr/bin/env python3
"""Export command-line interface for MediaWiki to Wiki.js migration tool.

This script exports content from MediaWiki, including pages, images, and links.
Supports resumable operations via checkpoints and dry-run mode.
"""

import argparse
import sys
from pathlib import Path
from typing import List, Optional

from src.lib.config import load_config
from src.lib.logger import setup_logger, CSVErrorLogger
from src.lib.storage_manager import StorageManager
from src.lib.mediawiki_client import MediaWikiClient
from src.lib.image_processor import ImageProcessor
from src.lib.link_traversal import LinkTraversal
from src.lib.content_transformer import ContentTransformer
from src.models import WikiPage, ImageAsset, Checkpoint, MigrationReport


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description='Export content from MediaWiki for migration to Wiki.js',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export with default settings (from .env)
  python export.py

  # Export specific namespaces
  python export.py --namespaces 0 1 2

  # Export from starting page with BFS link traversal
  python export.py --start-page "Main Page" --max-depth 2

  # Dry-run to see what would be exported
  python export.py --dry-run

  # Resume from checkpoint
  python export.py --resume

  # Export with custom output directory
  python export.py --output /path/to/export
        """
    )

    # Export mode
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        '--namespaces',
        type=int,
        nargs='+',
        help='Namespace IDs to export (default: 0=Main)'
    )
    mode_group.add_argument(
        '--start-page',
        type=str,
        help='Starting page for BFS link traversal'
    )

    # BFS options
    parser.add_argument(
        '--max-depth',
        type=int,
        default=-1,
        help='Maximum link depth for BFS traversal (-1 = unlimited)'
    )

    # Output options
    parser.add_argument(
        '--output',
        type=str,
        help='Export output directory (overrides .env)'
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
        help='Show what would be exported without saving files'
    )
    parser.add_argument(
        '--skip-images',
        action='store_true',
        help='Skip image downloads'
    )
    parser.add_argument(
        '--limit',
        type=int,
        help='Limit number of pages to export'
    )
    parser.add_argument(
        '--transform',
        action='store_true',
        help='Transform content to Wiki.js format (wikitext to markdown)'
    )
    parser.add_argument(
        '--skip-transform',
        action='store_true',
        help='Skip content transformation (keep wikitext)'
    )

    # Logging options
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Logging level (overrides .env)'
    )

    return parser.parse_args()


def get_pages_to_export(
    client: MediaWikiClient,
    args: argparse.Namespace,
    logger
) -> List[dict]:
    """Determine which pages to export based on arguments.

    Args:
        client: MediaWiki API client
        args: Parsed command-line arguments
        logger: Logger instance

    Returns:
        List of page dictionaries with 'title' and 'depth' fields
    """
    if args.start_page:
        # BFS traversal mode
        logger.info(f"Using BFS traversal starting from: {args.start_page}")

        traversal = LinkTraversal(max_depth=args.max_depth)
        pages = traversal.get_pages_to_process(
            start_page=args.start_page,
            get_links_callback=client.get_page_links
        )

        logger.info(f"BFS found {len(pages)} pages to export")
        return pages

    else:
        # Namespace listing mode
        namespaces = args.namespaces or [0]  # Default to Main namespace
        logger.info(f"Exporting from namespaces: {namespaces}")

        pages_raw = client.list_all_pages(
            namespaces=namespaces,
            limit=args.limit
        )

        # Convert to format with depth=0
        pages = [{'title': p['title'], 'depth': 0} for p in pages_raw]

        logger.info(f"Found {len(pages)} pages to export")
        return pages


def export_page(
    client: MediaWikiClient,
    storage: StorageManager,
    image_processor: ImageProcessor,
    page_title: str,
    page_depth: int,
    skip_images: bool,
    dry_run: bool,
    logger
) -> Optional[WikiPage]:
    """Export a single page with its content and images.

    Args:
        client: MediaWiki API client
        storage: Storage manager
        image_processor: Image processor
        page_title: Page title to export
        page_depth: Link depth (for BFS mode)
        skip_images: Whether to skip image downloads
        dry_run: Whether this is a dry-run
        logger: Logger instance

    Returns:
        WikiPage object if successful, None otherwise
    """
    try:
        # Get page content
        logger.info(f"Fetching page: {page_title}")
        page = client.get_page_content(page_title)

        if not page:
            logger.warning(f"Page not found: {page_title}")
            return None

        # Get categories
        categories = client.get_page_categories(page_title)
        page.categories = categories
        logger.debug(f"Found {len(categories)} categories")

        # Get links
        links = client.get_page_links(page_title)
        page.links = links
        logger.debug(f"Found {len(links)} links")

        # Get images
        image_names = client.get_page_images(page_title)
        logger.debug(f"Found {len(image_names)} images")

        images: List[ImageAsset] = []
        if not skip_images and image_names:
            for img_name in image_names:
                img_asset = client.get_image_info(img_name)
                if img_asset:
                    img_asset.page_references = [page_title]
                    images.append(img_asset)

        page.images = image_names

        if dry_run:
            logger.info(f"[DRY-RUN] Would export: {page_title}")
            logger.info(f"[DRY-RUN]   Categories: {len(categories)}")
            logger.info(f"[DRY-RUN]   Links: {len(links)}")
            logger.info(f"[DRY-RUN]   Images: {len(images)}")
            return page

        # Save page markdown
        page_slug = image_processor.generate_page_slug(page_title)
        storage.save_page_markdown(page, page.namespace)
        logger.info(f"Saved page: {page_title}")

        # Download and save images
        if images:
            # Rename images
            image_processor.rename_images(images, page_slug)

            # Download each image
            for img in images:
                img_dir = storage.create_images_dir(page.namespace)
                dest_path = img_dir / img.renamed_filename

                if image_processor.download_image(img, str(dest_path)):
                    logger.debug(f"Downloaded image: {img.renamed_filename}")
                else:
                    logger.warning(f"Failed to download: {img.original_filename}")

        return page

    except Exception as e:
        logger.error(f"Error exporting page '{page_title}': {e}")
        return None


def main():
    """Main export function."""
    # Parse arguments
    args = parse_arguments()

    # Load configuration
    config = load_config()

    # Override config with command-line arguments
    if args.output:
        config.export_dir = Path(args.output)
    if args.checkpoint_frequency:
        config.checkpoint_frequency = args.checkpoint_frequency
    if args.log_level:
        config.log_level = args.log_level

    # Setup logging
    logger = setup_logger('export', level=config.log_level)
    logger.info("=" * 80)
    logger.info("MediaWiki Export Tool")
    logger.info("=" * 80)

    if args.dry_run:
        logger.info("DRY-RUN MODE: No files will be saved")

    # Initialize components
    storage = StorageManager(config.export_dir)
    error_logger = CSVErrorLogger(config.export_dir / 'errors.csv')
    image_processor = ImageProcessor(error_logger)

    # Initialize MediaWiki client
    logger.info("Connecting to MediaWiki...")
    client = MediaWikiClient(
        url=config.mediawiki_url,
        username=config.mediawiki_username,
        password=config.mediawiki_password
    )

    if not client.login():
        logger.error("Failed to connect to MediaWiki")
        sys.exit(1)

    # Load or create checkpoint
    checkpoint: Optional[Checkpoint] = None
    if args.resume:
        checkpoint = storage.load_checkpoint()
        if checkpoint:
            logger.info(f"Resuming from checkpoint: {checkpoint.pages_processed} pages processed")
        else:
            logger.warning("No checkpoint found, starting fresh export")
            checkpoint = Checkpoint.create_new()
    else:
        checkpoint = Checkpoint.create_new()

    # Get pages to export
    pages = get_pages_to_export(client, args, logger)

    if not pages:
        logger.warning("No pages found to export")
        sys.exit(0)

    # Filter already processed pages if resuming
    if args.resume and checkpoint:
        original_count = len(pages)
        pages = [p for p in pages if not checkpoint.should_skip(p['title'])]
        skipped = original_count - len(pages)
        if skipped > 0:
            logger.info(f"Skipping {skipped} already processed pages")

    # Apply limit if specified
    if args.limit and len(pages) > args.limit:
        pages = pages[:args.limit]
        logger.info(f"Limited to {args.limit} pages")

    # Initialize migration report
    report = MigrationReport.create()

    # Export each page
    logger.info(f"Exporting {len(pages)} pages...")
    logger.info("")

    try:
        for idx, page_info in enumerate(pages, start=1):
            page_title = page_info['title']
            page_depth = page_info.get('depth', 0)

            logger.info(f"[{idx}/{len(pages)}] Processing: {page_title} (depth={page_depth})")

            # Export page
            page = export_page(
                client=client,
                storage=storage,
                image_processor=image_processor,
                page_title=page_title,
                page_depth=page_depth,
                skip_images=args.skip_images,
                dry_run=args.dry_run,
                logger=logger
            )

            if page:
                report.pages_exported_success += 1
                checkpoint.mark_page_processed(page.id, page.title)
            else:
                report.pages_exported_failed += 1
                report.add_error(page_title, 'export_failed', 'Failed to export page')

            # Save checkpoint periodically
            if not args.dry_run and idx % config.checkpoint_frequency == 0:
                storage.save_checkpoint(checkpoint)
                logger.info(f"Checkpoint saved ({checkpoint.pages_processed} pages)")

            logger.info("")

    except KeyboardInterrupt:
        logger.warning("Export interrupted by user")
        if not args.dry_run:
            storage.save_checkpoint(checkpoint)
            logger.info("Checkpoint saved")
        sys.exit(130)

    # Transform content if requested
    if args.transform and not args.skip_transform and report.pages_exported_success > 0:
        logger.info("")
        logger.info("=" * 80)
        logger.info("CONTENT TRANSFORMATION PHASE")
        logger.info("=" * 80)
        logger.info("Converting wikitext to markdown and transforming links...")

        try:
            # Initialize transformer
            def error_callback(page_title, error_type, message):
                report.add_error(page_title, error_type, message)
                error_logger.log_error('', page_title, error_type, message)

            transformer = ContentTransformer(error_callback=error_callback)

            # Load all exported pages
            exported_pages = storage.list_pages()
            logger.info(f"Found {len(exported_pages)} pages to transform")

            # Build image mapping (original -> renamed)
            image_mapping = {}
            for page_path in exported_pages:
                # Load page
                page_data = storage.load_export_metadata()
                # For now, we'll transform without image mapping
                # Image mapping will be built during export
                pass

            # Transform each page
            transform_success = 0
            transform_failed = 0

            for idx, page_path in enumerate(exported_pages, start=1):
                # Read page markdown file
                content = page_path.read_text(encoding='utf-8')

                # Extract page title from path
                page_title = page_path.stem

                logger.info(f"[{idx}/{len(exported_pages)}] Transforming: {page_title}")

                # Create WikiPage object for transformation
                temp_page = WikiPage(
                    id=str(idx),
                    title=page_title,
                    namespace="Main",
                    content=content
                )

                # Transform
                if transformer.transform_page(temp_page, image_mapping):
                    # Save transformed content
                    if not args.dry_run:
                        page_path.write_text(temp_page.content, encoding='utf-8')
                    transform_success += 1
                else:
                    transform_failed += 1

            logger.info("")
            logger.info(f"Transformation complete: {transform_success} succeeded, {transform_failed} failed")

        except Exception as e:
            logger.error(f"Transformation phase failed: {e}")
            report.add_error('transformation', 'transformation_phase_failed', str(e))

    # Complete report
    report.complete()

    # Final checkpoint save
    if not args.dry_run:
        storage.save_checkpoint(checkpoint)
        logger.info("Final checkpoint saved")

    # Delete checkpoint if export is complete
    if not args.dry_run and report.pages_exported_success == len(pages):
        storage.delete_checkpoint()
        logger.info("Export complete, checkpoint deleted")

    # Print summary
    logger.info("")
    logger.info("=" * 80)
    logger.info("EXPORT SUMMARY")
    logger.info("=" * 80)
    logger.info(f"Pages exported: {report.pages_exported_success}")
    logger.info(f"Pages failed: {report.pages_exported_failed}")
    logger.info(f"Duration: {report.duration_seconds():.1f} seconds")

    if report.errors:
        logger.warning(f"Errors encountered: {len(report.errors)}")
        logger.info(f"See {config.export_dir / 'errors.csv'} for details")

    # Save report
    if not args.dry_run:
        report_path = config.export_dir / 'export_report.json'
        with open(report_path, 'w') as f:
            f.write(report.to_json())
        logger.info(f"Report saved to: {report_path}")

    logger.info("=" * 80)

    # Exit with appropriate code
    if report.pages_exported_failed > 0:
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == '__main__':
    main()
