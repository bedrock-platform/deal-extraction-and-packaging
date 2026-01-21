"""
Google Sheets upload module for Google Authorized Buyers inventory data.

Handles uploading TSV data to Google Sheets with proper formatting and batching.
"""

import logging
from pathlib import Path
from typing import Optional

import pandas as pd

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


class GoogleSheetsUploader:
    """Handles uploading data to Google Sheets."""
    
    def __init__(self, google_sheets_id: Optional[str] = None):
        """
        Initialize Google Sheets uploader.
        
        Args:
            google_sheets_id: Google Sheets spreadsheet ID (from environment if not provided)
        """
        self.google_sheets_id = google_sheets_id
    
    def upload_tsv(
        self,
        tsv_path: Path,
        worksheet_name: str = "Marketplace"
    ) -> bool:
        """
        Upload TSV data to Google Sheets.
        
        Args:
            tsv_path: Path to the TSV file to upload
            worksheet_name: Name of the worksheet to upload to
            
        Returns:
            True if upload successful, False otherwise
        """
        if not self.google_sheets_id:
            logger.warning("GOOGLE_SHEETS_ID not set in .env. Skipping Google Sheets upload.")
            return False
        
        if not GSPREAD_AVAILABLE:
            logger.warning("gspread library not available. Skipping Google Sheets upload.")
            return False
        
        try:
            # Find service account credentials
            service_account_path = self._find_service_account_file()
            
            if not service_account_path or not service_account_path.exists():
                logger.warning(f"Service account JSON file not found in auth/ directory. Skipping Google Sheets upload.")
                return False
            
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
            
            # Read TSV file
            df = pd.read_csv(tsv_path, sep='\t')
            
            # Prepare data for upload
            df = self._prepare_dataframe(df)
            
            # Get or create worksheet
            worksheet = self._get_or_create_worksheet(spreadsheet, worksheet_name)
            
            # Clear and write data
            worksheet.clear()
            worksheet.update([df.columns.values.tolist()], 'A1')
            
            # Write data in batches
            if len(df) > 0:
                self._write_dataframe_batches(worksheet, df)
            
            logger.info(f"✅ Successfully uploaded {len(df)} rows to Google Sheets: {spreadsheet.url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to upload to Google Sheets: {e}")
            import traceback
            logger.debug(traceback.format_exc())
            return False
    
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
    
    def _prepare_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare DataFrame for Google Sheets upload.
        
        Args:
            df: Input DataFrame
            
        Returns:
            Prepared DataFrame
        """
        # Replace NaN values with empty strings (Google Sheets API doesn't accept NaN)
        df = df.fillna('')
        
        # Truncate long text fields to avoid Google Sheets 50,000 character limit
        for col in df.columns:
            if df[col].dtype == 'object':  # String columns
                # Truncate to 49,000 chars (leave buffer for formatting)
                df[col] = df[col].astype(str).apply(lambda x: x[:49000] if len(str(x)) > 49000 else x)
        
        # Convert all values to strings to avoid JSON serialization issues
        # This ensures compatibility with Google Sheets API
        df = df.astype(str)
        
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
            values = batch.values.tolist()
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
