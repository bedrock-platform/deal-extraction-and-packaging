"""
Unified Data Exporter

Handles export of multi-vendor deal data to various formats.
Supports JSON and CSV/TSV export with vendor tagging.
Also supports Google Sheets upload with separate worksheets per vendor.
"""
import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)

# Google Sheets integration (imported after logger is defined)
GSPREAD_AVAILABLE = False
try:
    import gspread
    from google.oauth2.service_account import Credentials
    GSPREAD_AVAILABLE = True
except ImportError:
    logger.warning(
        "gspread library not installed. Google Sheets upload will not be available. "
        "Install with: pip install gspread google-auth google-auth-oauthlib"
    )


def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_', exclude_keys: Optional[set] = None) -> Dict[str, Any]:
    """
    Flatten nested dictionary for CSV/TSV export.
    
    Example:
        {"taxonomy": {"tier1": "Automotive", "tier2": "Parts"}}
        -> {"taxonomy_tier1": "Automotive", "taxonomy_tier2": "Parts"}
    
    Args:
        d: Dictionary to flatten
        parent_key: Parent key prefix (for recursion)
        sep: Separator for nested keys
        exclude_keys: Set of keys to exclude from flattening (kept as JSON string)
        
    Returns:
        Flattened dictionary
    """
    if exclude_keys is None:
        exclude_keys = set()
    
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        
        # If this key should be excluded, keep it as JSON string
        if k in exclude_keys or (parent_key == '' and k in exclude_keys):
            items.append((k, json.dumps(v) if v else ''))
        elif isinstance(v, dict):
            # Recursively flatten nested dicts
            items.extend(flatten_dict(v, new_key, sep=sep, exclude_keys=exclude_keys).items())
        elif isinstance(v, list):
            # Convert lists to JSON strings for CSV compatibility
            items.append((new_key, json.dumps(v) if v else ''))
        else:
            items.append((new_key, v))
    
    return dict(items)


class UnifiedDataExporter:
    """
    Unified data exporter for multi-vendor deal extraction.
    
    Handles export of deals from multiple vendors to JSON and CSV/TSV formats.
    Supports vendor-specific schemas and unified exports.
    Also supports Google Sheets upload with separate worksheets per vendor.
    """
    
    # Mapping of vendor names to worksheet names
    VENDOR_WORKSHEET_MAP = {
        "Google Authorized Buyers": "Google Marketplace",
        "Google Curated": "Google Curated",
        "BidSwitch": "BidSwitch",
        "google_ads": "Google Marketplace",
        "google_curated": "Google Curated",
        "bidswitch": "BidSwitch",
    }
    
    def __init__(self, output_dir: Path, google_sheets_id: Optional[str] = None):
        """
        Initialize unified data exporter.
        
        Args:
            output_dir: Directory where output files will be saved
            google_sheets_id: Google Sheets spreadsheet ID (reads from GOOGLE_SHEETS_ID env var if None)
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
        self.google_sheets_id = google_sheets_id or os.getenv('GOOGLE_SHEETS_ID')
        logger.info(f"Initialized unified data exporter with output directory: {self.output_dir}")
        if self.google_sheets_id:
            logger.info(f"Google Sheets ID configured: {self.google_sheets_id}")
    
    def save_json(
        self,
        deals: Dict[str, List[Dict]],
        timestamp: Optional[str] = None,
        vendor: Optional[str] = None
    ) -> Path:
        """
        Save deals to JSON file with timestamp.
        
        Args:
            deals: Dictionary mapping vendor name -> list of deals, OR list of deals if vendor specified
            timestamp: Optional ISO 8601 timestamp string (generated if not provided)
            vendor: Optional vendor name (if provided, deals should be a list)
            
        Returns:
            Path to the saved JSON file
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
        
        if vendor:
            # Single vendor export
            filename = f"{vendor.lower().replace(' ', '_')}_{timestamp}.json"
            data = deals if isinstance(deals, list) else deals.get(vendor, [])
        else:
            # Multi-vendor export
            filename = f"deals_{timestamp}.json"
            data = deals
        
        filepath = self.output_dir / filename
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved JSON file: {filepath}")
        return filepath
    
    def export_to_csv(
        self,
        deals: Dict[str, List[Dict]],
        timestamp: Optional[str] = None,
        vendor: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Export deals to CSV/TSV files.
        
        Args:
            deals: Dictionary mapping vendor name -> list of transformed deals, OR list if vendor specified
            timestamp: Optional ISO 8601 timestamp string
            vendor: Optional vendor name (if provided, deals should be a list)
            
        Returns:
            Dictionary mapping file type to file path
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
        
        output_files = {}
        
        if vendor:
            # Single vendor export
            deals_list = deals if isinstance(deals, list) else deals.get(vendor, [])
            if deals_list:
                # Flatten nested structures for CSV/TSV
                flattened_deals = [flatten_dict(deal) for deal in deals_list]
                df = pd.DataFrame(flattened_deals)
                # Use worksheet name for filename consistency
                worksheet_name = self._get_worksheet_name(vendor)
                filename_base = self._worksheet_name_to_filename(worksheet_name)
                filename = f"{filename_base}_{timestamp}.tsv"
                filepath = self.output_dir / filename
                df.to_csv(filepath, index=False, sep='	')
                output_files["tsv"] = filepath
                logger.info(f"Saved TSV file: {filepath} ({len(deals_list)} rows)")
        else:
            # Multi-vendor export - create separate files per vendor
            for vendor_name, vendor_deals in deals.items():
                if vendor_deals:
                    # Flatten nested structures for CSV/TSV
                    flattened_deals = [flatten_dict(deal) for deal in vendor_deals]
                    df = pd.DataFrame(flattened_deals)
                    # Use worksheet name for filename consistency
                    worksheet_name = self._get_worksheet_name(vendor_name)
                    filename_base = self._worksheet_name_to_filename(worksheet_name)
                    filename = f"{filename_base}_{timestamp}.tsv"
                    filepath = self.output_dir / filename
                    df.to_csv(filepath, index=False, sep='	')
                    output_files[f"{vendor_name}_tsv"] = filepath
                    logger.info(f"Saved {vendor_name} TSV: {filepath} ({len(vendor_deals)} rows)")
            
            # Also create unified export with vendor column
            all_deals = []
            for vendor_name, vendor_deals in deals.items():
                for deal in vendor_deals:
                    deal_with_vendor = deal.copy()
                    if "vendor" not in deal_with_vendor:
                        deal_with_vendor["vendor"] = vendor_name
                    all_deals.append(deal_with_vendor)
            
            if all_deals:
                # For unified TSV: exclude raw_deal_data from flattening, keep it as JSON string
                # This prevents vendor-specific columns from polluting the unified schema
                flattened_deals = [
                    flatten_dict(deal, exclude_keys={'raw_deal_data'}) 
                    for deal in all_deals
                ]
                df_unified = pd.DataFrame(flattened_deals)
                
                # Ensure raw_deal_data is present as a JSON string column (if it exists in any deal)
                if 'raw_deal_data' not in df_unified.columns:
                    # Extract raw_deal_data from original deals and add as JSON string
                    raw_deal_data_col = []
                    for deal in all_deals:
                        raw_deal_data_col.append(json.dumps(deal.get('raw_deal_data', {})))
                    df_unified['raw_deal_data'] = raw_deal_data_col
                
                # Ensure source column comes before ssp_name
                cols = list(df_unified.columns)
                if "source" in cols and "ssp_name" in cols:
                    source_idx = cols.index("source")
                    ssp_idx = cols.index("ssp_name")
                    if source_idx > ssp_idx:
                        cols.remove("source")
                        cols.insert(ssp_idx, "source")
                        df_unified = df_unified[cols]
                
                filename = f"deals_unified_{timestamp}.tsv"
                filepath = self.output_dir / filename
                df_unified.to_csv(filepath, index=False, sep='	')
                output_files["unified_tsv"] = filepath
                logger.info(f"Saved unified TSV: {filepath} ({len(all_deals)} rows, {len(df_unified.columns)} columns)")
        
        return output_files
    
    def _get_worksheet_name(self, vendor_name: str) -> str:
        """
        Get worksheet name for a vendor.
        
        Args:
            vendor_name: Vendor name
            
        Returns:
            Worksheet name
        """
        return self.VENDOR_WORKSHEET_MAP.get(vendor_name, vendor_name)
    
    def _worksheet_name_to_filename(self, worksheet_name: str) -> str:
        """
        Convert worksheet name to filename-safe format.
        
        Args:
            worksheet_name: Worksheet name (e.g., "Google Marketplace")
            
        Returns:
            Filename-safe string (e.g., "google_marketplace")
        """
        # Convert to lowercase and replace spaces with underscores
        return worksheet_name.lower().replace(' ', '_')
    
    def upload_to_google_sheets(
        self,
        results: Dict[str, List[Dict]],
        tsv_files: Optional[Dict[str, Path]] = None
    ) -> Dict[str, bool]:
        """
        Upload vendor data to Google Sheets, creating separate worksheets per vendor.
        
        Args:
            results: Dictionary mapping vendor name -> list of transformed deals
            tsv_files: Optional dictionary mapping vendor name -> TSV file path (if None, will create from results)
            
        Returns:
            Dictionary mapping vendor name -> upload success status
        """
        if not self.google_sheets_id:
            logger.warning("GOOGLE_SHEETS_ID not set. Skipping Google Sheets upload.")
            return {}
        
        if not GSPREAD_AVAILABLE:
            logger.warning("gspread library not available. Skipping Google Sheets upload.")
            return {}
        
        upload_results = {}
        
        try:
            # Find service account credentials
            service_account_path = self._find_service_account_file()
            
            if not service_account_path or not service_account_path.exists():
                logger.warning("Service account JSON file not found in auth/ directory. Skipping Google Sheets upload.")
                return {}
            
            # Authenticate with Google Sheets API
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                str(service_account_path),
                scopes=scopes
            )
            client = gspread.authorize(creds)
            
            # Open the spreadsheet
            spreadsheet = client.open_by_key(self.google_sheets_id)
            
            # Upload each vendor's data to its own worksheet
            for vendor_name, vendor_deals in results.items():
                if not vendor_deals:
                    logger.info(f"No deals for {vendor_name}, skipping Google Sheets upload")
                    upload_results[vendor_name] = False
                    continue
                
                worksheet_name = self._get_worksheet_name(vendor_name)
                
                # Get TSV file path if provided, otherwise create DataFrame from results
                if tsv_files:
                    # Find matching TSV file
                    tsv_path = None
                    for key, path in tsv_files.items():
                        if vendor_name.lower().replace(' ', '_') in key.lower() or key == "tsv":
                            tsv_path = path
                            break
                    
                    if tsv_path and tsv_path.exists():
                        df = pd.read_csv(tsv_path, sep='	')
                    else:
                        # Flatten nested structures for Google Sheets
                        flattened_deals = [flatten_dict(deal) for deal in vendor_deals]
                        df = pd.DataFrame(flattened_deals)
                else:
                    # Flatten nested structures for Google Sheets
                    flattened_deals = [flatten_dict(deal) for deal in vendor_deals]
                    df = pd.DataFrame(flattened_deals)
                
                # Upload to worksheet
                success = self._upload_dataframe_to_worksheet(spreadsheet, df, worksheet_name)
                upload_results[vendor_name] = success
                
                if success:
                    logger.info(f"✅ Successfully uploaded {len(df)} rows from {vendor_name} to worksheet '{worksheet_name}'")
            
            return upload_results
            
        except Exception as e:
            logger.error(f"Failed to upload to Google Sheets: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return upload_results
    
    def _find_service_account_file(self) -> Optional[Path]:
        """
        Find service account JSON file in auth/ directory.
        
        Returns:
            Path to service account file, or None if not found
        """
        auth_dir = Path("auth")
        
        if not auth_dir.exists():
            return None
        
        # Look for bedrock service account file
        bedrock_file = auth_dir / "bedrock-us-east-e94069e89afa.json"
        if bedrock_file.exists():
            return bedrock_file
        
        # Look for any JSON file in auth/
        json_files = list(auth_dir.glob("*.json"))
        if json_files:
            return json_files[0]
        
        return None
    
    def _get_spreadsheet(self):
        """
        Get authenticated Google Sheets spreadsheet object.
        
        Returns:
            gspread Spreadsheet object, or None if authentication fails
        """
        if not self.google_sheets_id:
            return None
        
        if not GSPREAD_AVAILABLE:
            return None
        
        try:
            service_account_path = self._find_service_account_file()
            if not service_account_path or not service_account_path.exists():
                return None
            
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                str(service_account_path),
                scopes=scopes
            )
            client = gspread.authorize(creds)
            return client.open_by_key(self.google_sheets_id)
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            return None
    
        """
        Find service account JSON file in auth/ directory.
        
        Returns:
            Path to service account file, or None if not found
        """
        auth_dir = Path("auth")
        
        if not auth_dir.exists():
            return None

        auth_dir = Path("auth")

        if not auth_dir.exists():
            return None

        # Look for bedrock service account file
        bedrock_file = auth_dir / "bedrock-us-east-e94069e89afa.json"
        if bedrock_file.exists():
            return bedrock_file

        # Look for any JSON file in auth/
        json_files = list(auth_dir.glob("*.json"))
        if json_files:
            return json_files[0]

        return None

        """
        Get authenticated Google Sheets spreadsheet object.
        
        Returns:
            gspread Spreadsheet object, or None if authentication fails
        """
        if not self.google_sheets_id:
            return None
        
        if not GSPREAD_AVAILABLE:
            return None
        
        try:
            service_account_path = self._find_service_account_file()
            if not service_account_path or not service_account_path.exists():
                return None
            
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            creds = Credentials.from_service_account_file(
                str(service_account_path),
                scopes=scopes
            )
            client = gspread.authorize(creds)
            return client.open_by_key(self.google_sheets_id)
        except Exception as e:
            logger.error(f"Failed to authenticate with Google Sheets: {e}")
            return None
    
    def _upload_dataframe_to_worksheet(
        self,
        spreadsheet,
        df: pd.DataFrame,
        worksheet_name: str
    ) -> bool:
        """
        Upload a DataFrame to a Google Sheets worksheet.
        
        Args:
            spreadsheet: gspread Spreadsheet object
            df: DataFrame to upload
            worksheet_name: Name of worksheet
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Prepare DataFrame
            df = self._prepare_dataframe(df)
            
            # Get or create worksheet
            worksheet = self._get_or_create_worksheet(spreadsheet, worksheet_name)
            
            # Clear and write data
            worksheet.clear()
            worksheet.update([df.columns.values.tolist()], 'A1')
            
            # Write data in batches
            if len(df) > 0:
                self._write_dataframe_batches(worksheet, df)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload DataFrame to worksheet '{worksheet_name}': {e}")
            return False
    
    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare DataFrame for Google Sheets upload.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Prepared DataFrame
        """
        # Create a copy to avoid modifying original
        df = df.copy()
        
        # Process each column based on its type
        for col in df.columns:
            if df[col].dtype == 'object':  # String/object columns
                # Replace NaN with empty string for string columns
                df[col] = df[col].fillna('')
                # Convert to string and truncate long text fields to avoid Google Sheets 50,000 character limit
                df[col] = df[col].astype(str).apply(lambda x: x[:49000] if len(str(x)) > 49000 else x)
            elif pd.api.types.is_numeric_dtype(df[col]):
                # For numeric columns, replace NaN with None (becomes empty cell in Google Sheets)
                # Keep as numeric type - Google Sheets API handles Python int/float natively
                df[col] = df[col].where(pd.notna(df[col]), None)
            elif pd.api.types.is_bool_dtype(df[col]):
                # For boolean columns, replace NaN with None
                df[col] = df[col].where(pd.notna(df[col]), None)
            else:
                # For other types (datetime, etc.), convert to string and handle NaN
                df[col] = df[col].fillna('').astype(str)
        
        return df
    
    def _get_or_create_worksheet(self, spreadsheet, worksheet_name: str):
        """
        Get existing worksheet or create new one.
        
        Args:
            spreadsheet: gspread Spreadsheet object
            worksheet_name: Name of worksheet
            
        Returns:
            gspread Worksheet object
        """
        try:
            worksheet = spreadsheet.worksheet(worksheet_name)
            return worksheet
        except:
            # Create new worksheet if it doesn't exist
            # Estimate rows/cols from first worksheet or use defaults
            try:
                first_sheet = spreadsheet.sheet1
                rows = len(first_sheet.get_all_values()) + 1 if first_sheet else 1000
                cols = len(first_sheet.row_values(1)) if first_sheet else 50
            except:
                rows, cols = 1000, 50
            
            worksheet = spreadsheet.add_worksheet(
                title=worksheet_name,
                rows=rows,
                cols=cols
            )
            return worksheet
    
    def export_packages_to_google_sheets(
        self,
        packages: List[Dict[str, Any]],
        worksheet_name: str = "Packages Enriched 1"
    ) -> bool:
        """
        Export packages to Google Sheets worksheet.
        
        Args:
            packages: List of package dictionaries from Stage 2
            worksheet_name: Name of the worksheet (default: "Packages Enriched 1")
            
        Returns:
            True if successful, False otherwise
        """
        if not self.google_sheets_id:
            logger.warning("GOOGLE_SHEETS_ID not set. Skipping Google Sheets upload.")
            return False
        
        if not GSPREAD_AVAILABLE:
            logger.warning("gspread library not available. Skipping Google Sheets upload.")
            return False
        
        if not packages:
            logger.warning(f"No packages to upload to '{worksheet_name}'")
            return False
        
        try:
            spreadsheet = self._get_spreadsheet()
            if not spreadsheet:
                return False
            
            # Flatten nested structures for Google Sheets
            flattened_packages = [flatten_dict(pkg) for pkg in packages]
            df = pd.DataFrame(flattened_packages)
            
            # Prepare DataFrame for Google Sheets
            df = self._prepare_dataframe(df)
            
            # Upload to worksheet
            success = self._upload_dataframe_to_worksheet(spreadsheet, df, worksheet_name)
            
            if success:
                logger.info(f"✅ Successfully uploaded {len(df)} packages to worksheet '{worksheet_name}'")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to upload packages to Google Sheets: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def export_enriched_packages_to_google_sheets(
        self,
        enriched_packages: List[Dict[str, Any]],
        worksheet_name: str = "Packages Enriched 2"
    ) -> bool:
        """
        Export enriched packages to Google Sheets worksheet.
        
        Args:
            enriched_packages: List of enriched package dictionaries from Stage 3
            worksheet_name: Name of the worksheet (default: "Packages Enriched 2")
            
        Returns:
            True if successful, False otherwise
        """
        if not self.google_sheets_id:
            logger.warning("GOOGLE_SHEETS_ID not set. Skipping Google Sheets upload.")
            return False
        
        if not GSPREAD_AVAILABLE:
            logger.warning("gspread library not available. Skipping Google Sheets upload.")
            return False
        
        if not enriched_packages:
            logger.warning(f"No enriched packages to upload to '{worksheet_name}'")
            return False
        
        try:
            spreadsheet = self._get_spreadsheet()
            if not spreadsheet:
                return False
            
            # Flatten nested structures for Google Sheets
            flattened_packages = [flatten_dict(pkg) for pkg in enriched_packages]
            df = pd.DataFrame(flattened_packages)
            
            # Prepare DataFrame for Google Sheets
            df = self._prepare_dataframe(df)
            
            # Upload to worksheet
            success = self._upload_dataframe_to_worksheet(spreadsheet, df, worksheet_name)
            
            if success:
                logger.info(f"✅ Successfully uploaded {len(df)} enriched packages to worksheet '{worksheet_name}'")
            
            return success
            
        except Exception as e:
            logger.error(f"Failed to upload enriched packages to Google Sheets: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
    def _write_dataframe_batches(self, worksheet, df: pd.DataFrame):
        """
        Write DataFrame to worksheet in batches to avoid API limits.
        
        Args:
            worksheet: gspread Worksheet object
            df: DataFrame to write
        """
        num_cols = len(df.columns)
        last_col_letter = self._num_to_col_letter(num_cols)
        
        # Split into batches of 1000 rows to avoid API limits
        batch_size = 1000
        for i in range(0, len(df), batch_size):
            batch = df.iloc[i:i+batch_size]
            
            # Convert to list, replacing NaN/NaT with None for JSON compatibility
            # This preserves numeric types while handling missing values
            values = []
            for _, row in batch.iterrows():
                row_values = []
                for val in row:
                    if pd.isna(val):
                        row_values.append(None)
                    else:
                        # Convert numpy types to Python native types for JSON compatibility
                        # This ensures numbers appear as numbers (not strings) in Google Sheets
                        if isinstance(val, (np.integer,)):
                            row_values.append(int(val))
                        elif isinstance(val, (np.floating,)):
                            row_values.append(float(val))
                        elif isinstance(val, (np.bool_,)):
                            row_values.append(bool(val))
                        else:
                            row_values.append(val)
                values.append(row_values)
            
            # Start row is 2 (after header), adjust for batch
            start_row = i + 2
            end_row = start_row + len(values) - 1
            range_name = f'A{start_row}:{last_col_letter}{end_row}'
            worksheet.update(values, range_name)
    
    def _num_to_col_letter(self, n: int) -> str:
        """
        Convert 1-based column number to Excel column letter.
        
        Args:
            n: Column number (1-based)
            
        Returns:
            Excel column letter (A, B, ..., Z, AA, AB, etc.)
        """
        result = ""
        while n > 0:
            n -= 1
            result = chr(65 + (n % 26)) + result
            n //= 26
        return result
    
    def export_multi_vendor(
        self,
        results: Dict[str, List[Dict]],
        timestamp: Optional[str] = None,
        upload_to_sheets: bool = True
    ) -> Dict[str, Path]:
        """
        Export multi-vendor results to files and optionally upload to Google Sheets.
        
        Args:
            results: Dictionary mapping vendor name -> list of transformed deals
            timestamp: Optional ISO 8601 timestamp string
            upload_to_sheets: If True, upload to Google Sheets after file export
            
        Returns:
            Dictionary mapping file type to file path
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
        
        output_files = {}
        
        # Save JSON (multi-vendor format)
        json_path = self.save_json(results, timestamp)
        output_files["json"] = json_path
        
        # Export CSV/TSV
        csv_files = self.export_to_csv(results, timestamp)
        output_files.update(csv_files)
        
        # Upload to Google Sheets if enabled
        if upload_to_sheets:
            upload_results = self.upload_to_google_sheets(results, csv_files)
            for vendor_name, success in upload_results.items():
                if success:
                    logger.info(f"Google Sheets upload for {vendor_name}: ✅ Success")
                else:
                    logger.warning(f"Google Sheets upload for {vendor_name}: ❌ Failed")
            
            # Also upload unified TSV to "Unified" worksheet
            if "unified_tsv" in csv_files:
                unified_tsv_path = csv_files["unified_tsv"]
                if unified_tsv_path and unified_tsv_path.exists():
                    spreadsheet = self._get_spreadsheet()
                    if spreadsheet:
                        try:
                            df_unified = pd.read_csv(unified_tsv_path, sep='	')
                            success = self._upload_dataframe_to_worksheet(spreadsheet, df_unified, "Unified")
                            if success:
                                logger.info(f"✅ Successfully uploaded unified TSV ({len(df_unified)} rows) to worksheet 'Unified'")
                            else:
                                logger.warning("❌ Failed to upload unified TSV to Google Sheets")
                        except Exception as e:
                            logger.error(f"Failed to upload unified TSV to Google Sheets: {e}")
                    else:
                        logger.warning("Could not authenticate with Google Sheets. Skipping unified TSV upload.")
        
        return output_files
