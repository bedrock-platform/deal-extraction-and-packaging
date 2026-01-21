"""
Deal Extraction - Google Authorized Buyers API Client

Extracts deal information and metadata from Google Authorized Buyers using the internal API endpoint.
This internal API provides data that is NOT available in the public Authorized Buyers Marketplace API.

Uses manual browser tokens (SAPISIDHASH) extracted from Chrome DevTools. We use the internal API endpoint because it's
the only source for forecast/breakdown discovery data.

Handles pagination, token expiration, and exports data to JSON and TSV/CSV formats.
"""

import json
import logging
import os
from datetime import datetime
from glob import glob
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv

from .api_client import APIClient
from .auth import AuthManager
from .data_export import DataExporter
from .google_sheets import GoogleSheetsUploader

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class InventoryDownloader:
    """Downloads inventory forecast data from Google Authorized Buyers internal API."""

    def __init__(self, debug: bool = False):
        """
        Initialize the downloader with configuration from environment variables.

        Supports two authentication methods (in priority order):
        1. SAPISIDHASH (AUTHORIZED_BUYERS_SAPISIDHASH + AUTHORIZED_BUYERS_COOKIES) - Manual browser tokens
        2. Bearer Token (AUTHORIZED_BUYERS_BEARER_TOKEN) - Manual bearer token

        Args:
            debug: If True, enable DEBUG level logging for request/response details
        """
        if debug:
            logging.getLogger().setLevel(logging.DEBUG)

        # Load configuration from environment
        self.account_id = os.getenv('AUTHORIZED_BUYERS_ACCOUNT_ID')
        self.api_key = os.getenv('AUTHORIZED_BUYERS_API_KEY')
        self.google_sheets_id = os.getenv('GOOGLE_SHEETS_ID')
        
        # Validate required configuration
        if not self.account_id:
            raise ValueError(
                "Missing required environment variable. "
                "Please ensure AUTHORIZED_BUYERS_ACCOUNT_ID is set in your .env file."
            )
        
        if not self.api_key:
            raise ValueError(
                "API key is required. Please ensure AUTHORIZED_BUYERS_API_KEY is set in your .env file.\n"
                "Note: This internal API provides forecast/breakdown discovery data not available in public APIs."
            )

        # Initialize authentication manager
        self.auth_manager = AuthManager()
        
        # Initialize API client
        self.api_client = APIClient(self.account_id, self.api_key, self.auth_manager)
        
        # Initialize data exporter
        self.output_dir = Path("output")
        if self.output_dir.exists():
            # Clear all files in output directory
            for file in self.output_dir.glob("*"):
                if file.is_file():
                    file.unlink()
                    logger.debug(f"Deleted old file: {file}")
            logger.info(f"Cleared output directory: {self.output_dir}")
        self.data_exporter = DataExporter(self.output_dir)
        
        # Initialize Google Sheets uploader
        self.sheets_uploader = GoogleSheetsUploader(self.google_sheets_id)

        logger.info(f"Initialized downloader for account: {self.account_id} (Auth: {self.auth_manager.auth_method})")

    def fetch_all_inventory(
        self,
        payload: Optional[Dict] = None,
        rate_limit_delay: float = 0.5
    ) -> List[Dict]:
        """
        Fetch all inventory entities with pagination support.

        Args:
            payload: Optional request payload (filters, etc.)
            rate_limit_delay: Delay between requests in seconds

        Returns:
            List of all inventory entities across all pages
        """
        return self.api_client.fetch_all_inventory(payload, rate_limit_delay)

    def save_json(self, entities: List[Dict], timestamp: Optional[str] = None) -> Path:
        """
        Save entities to JSON file with timestamp.

        Args:
            entities: List of entity dictionaries
            timestamp: Optional ISO 8601 timestamp string (generated if not provided)

        Returns:
            Path to the saved JSON file
        """
        return self.data_exporter.save_json(entities, timestamp)

    def hydrate_package_details(self, entity_ids: List[str]) -> Dict[str, Dict]:
        """
        Fetch package details (email, floor price, created by) for multiple entities.
        Uses threading for parallel requests with backoff to avoid rate limits.
        
        Args:
            entity_ids: List of entity IDs to fetch details for
            
        Returns:
            Dictionary mapping entity_id -> detail data
        """
        return self.api_client.hydrate_package_details(entity_ids)

    def export_to_csv(self, entities: List[Dict], timestamp: Optional[str] = None) -> Dict[str, Path]:
        """
        Export entities to a single comprehensive TSV file with all slice data flattened into columns.
        Also hydrates package details (email, floor price, created by) via parallel API calls.

        Args:
            entities: List of entity dictionaries
            timestamp: Optional ISO 8601 timestamp string (generated if not provided)

        Returns:
            Dictionary mapping file type to file path
        """
        # Hydrate package details (email, floor price, created by) for all entities
        entity_ids = [e.get("entityId") for e in entities if e.get("entityId")]
        package_details = self.hydrate_package_details(entity_ids) if entity_ids else {}

        return self.data_exporter.export_to_csv(entities, package_details, timestamp)

    def fetch_google_curated_packages(self, page_size: int = 20) -> List[Dict]:
        """
        Fetch all Google Curated packages with pagination support.
        
        Args:
            page_size: Number of packages per page
            
        Returns:
            List of all Google Curated packages across all pages
        """
        return self.api_client.fetch_google_curated_packages(page_size)

    def export_google_curated_to_csv(self, packages: List[Dict], timestamp: Optional[str] = None) -> Dict[str, Path]:
        """
        Export Google Curated packages to TSV file.
        Simplified structure since Google Curated doesn't have forecast breakdowns.
        
        Args:
            packages: List of Google Curated package dictionaries
            timestamp: Optional ISO 8601 timestamp string
            
        Returns:
            Dictionary mapping file type to file path
        """
        return self.data_exporter.export_google_curated_to_csv(packages, timestamp)

    def upload_to_google_sheets(self, tsv_path: Path, worksheet_name: str = "Marketplace") -> bool:
        """
        Upload TSV data to Google Sheets.
        
        Args:
            tsv_path: Path to the TSV file to upload
            worksheet_name: Name of the worksheet to upload to
            
        Returns:
            True if upload successful, False otherwise
        """
        return self.sheets_uploader.upload_tsv(tsv_path, worksheet_name)

    def download_and_export_google_curated(self, export_csv: bool = True) -> Dict[str, Path]:
        """
        Complete workflow: download Google Curated packages and export to files.
        
        Args:
            export_csv: If True, export TSV files in addition to JSON
            
        Returns:
            Dictionary mapping file type to file path
        """
        timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
        
        # Fetch all Google Curated packages
        packages = self.fetch_google_curated_packages()
        
        if not packages:
            logger.warning("No Google Curated packages found. No files will be created.")
            return {}
        
        # Save JSON
        json_path = self.output_dir / f"google_curated_{timestamp}.json"
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(packages, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved JSON file: {json_path}")
        output_files = {"json": json_path}
        
        # Export TSV if requested
        if export_csv:
            tsv_files = self.export_google_curated_to_csv(packages, timestamp)
            output_files.update(tsv_files)
            
            # Upload to Google Sheets if configured
            if "tsv" in tsv_files:
                self.upload_to_google_sheets(tsv_files["tsv"], worksheet_name="Google Curated")
        
        logger.info(f"Google Curated download and export complete. Files saved to: {self.output_dir}")
        return output_files

    def download_and_export(
        self,
        payload: Optional[Dict] = None,
        export_csv: bool = True
    ) -> Dict[str, Path]:
        """
        Complete workflow: download inventory and export to files.

        Args:
            payload: Optional request payload (filters, etc.)
            export_csv: If True, export TSV/CSV files in addition to JSON

        Returns:
            Dictionary mapping file type to file path
        """
        timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")

        # Fetch all entities
        entities = self.fetch_all_inventory(payload)

        if not entities:
            logger.warning("No entities found. No files will be created.")
            return {}

        # Save JSON
        json_path = self.save_json(entities, timestamp)
        output_files = {"json": json_path}

        # Export TSV if requested
        if export_csv:
            tsv_files = self.export_to_csv(entities, timestamp)
            output_files.update(tsv_files)
            
            # Upload to Google Sheets if configured
            if "tsv" in tsv_files:
                self.upload_to_google_sheets(tsv_files["tsv"], worksheet_name="Marketplace")

        logger.info(f"Download and export complete. Files saved to: {self.output_dir}")
        return output_files


def main():
    """Main entry point for command-line usage."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Download inventory forecast data from Google Authorized Buyers internal API"
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable DEBUG level logging for request/response details"
    )
    parser.add_argument(
        "--no-csv",
        action="store_true",
        help="Skip TSV/CSV export (only save JSON)"
    )
    parser.add_argument(
        "--payload",
        type=str,
        help="Path to JSON file containing request payload (filters, etc.)"
    )
    parser.add_argument(
        "--google-curated",
        action="store_true",
        help="Fetch Google Curated packages instead of Marketplace packages"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Fetch both Marketplace and Google Curated packages (populates both worksheets)"
    )

    args = parser.parse_args()
    
    # Validate arguments
    if args.all and args.google_curated:
        logger.error("Cannot use --all and --google-curated together. Use --all to fetch both, or --google-curated to fetch only Google Curated.")
        return 1

    try:
        # Initialize downloader
        downloader = InventoryDownloader(debug=args.debug)

        # Download and export based on type
        if args.all:
            # Fetch both Marketplace and Google Curated packages
            logger.info("="*60)
            logger.info("Fetching Marketplace packages...")
            logger.info("="*60)
            
            payload = None
            if args.payload:
                with open(args.payload, "r") as f:
                    payload = json.load(f)
                logger.info(f"Loaded payload from: {args.payload}")
            
            marketplace_files = downloader.download_and_export(
                payload=payload,
                export_csv=not args.no_csv
            )
            
            logger.info("\n" + "="*60)
            logger.info("Fetching Google Curated packages...")
            logger.info("="*60)
            
            curated_files = downloader.download_and_export_google_curated(
                export_csv=not args.no_csv
            )
            
            # Combine file dictionaries
            files = {**marketplace_files, **curated_files}
            
        elif args.google_curated:
            # Fetch Google Curated packages only
            files = downloader.download_and_export_google_curated(
                export_csv=not args.no_csv
            )
        else:
            # Fetch Marketplace packages only (default)
            payload = None
            if args.payload:
                with open(args.payload, "r") as f:
                    payload = json.load(f)
                logger.info(f"Loaded payload from: {args.payload}")
            
            files = downloader.download_and_export(
                payload=payload,
                export_csv=not args.no_csv
            )

        print("\n" + "="*60)
        print("Download Complete!")
        print("="*60)
        for file_type, filepath in files.items():
            print(f"{file_type.upper()}: {filepath}")

    except ValueError as e:
        logger.error(str(e))
        return 1
    except Exception as e:
        logger.exception("Unexpected error occurred")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
