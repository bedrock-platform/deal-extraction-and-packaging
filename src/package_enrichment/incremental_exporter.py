"""
Incremental Exporter for Package Enrichment (Stage 3)

Saves enriched packages immediately after enrichment and appends to Google Sheets.
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict, Any
import pandas as pd
import numpy as np

from ..common.data_exporter import flatten_dict

logger = logging.getLogger(__name__)


class EnrichedPackageIncrementalExporter:
    """
    Exports enriched packages incrementally (as they're enriched) to files and Google Sheets.
    
    Features:
    - Appends to JSON Lines file (one JSON object per line)
    - Appends to JSON file (array format, rewrites on each append)
    - Appends rows to Google Sheets incrementally
    """
    
    def __init__(
        self,
        output_dir: Path,
        timestamp: str,
        google_sheets_id: Optional[str] = None
    ):
        """
        Initialize incremental exporter.
        
        Args:
            output_dir: Output directory for files
            timestamp: Timestamp string for filenames
            google_sheets_id: Optional Google Sheets spreadsheet ID
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.timestamp = timestamp
        
        # File paths
        self.jsonl_path = output_dir / f"packages_enriched_{timestamp}.jsonl"
        self.json_path = output_dir / f"packages_enriched_{timestamp}.json"
        
        # Track if JSON array has been initialized
        self.json_initialized = self.json_path.exists()
        
        # Google Sheets
        self.google_sheets_id = google_sheets_id
        self.worksheet = None
        self.sheets_header_written = False
        self.sheets_header_columns = None
        self.sheets_next_row = 2  # Row 1 is header
        
        # Initialize Google Sheets if configured
        if google_sheets_id:
            self._init_google_sheets()
    
    def _get_column_letter(self, col_num: int) -> str:
        """Convert column number (1-based) to Google Sheets column letter (A, B, ..., Z, AA, ...)."""
        result = ""
        while col_num > 0:
            col_num -= 1
            result = chr(65 + (col_num % 26)) + result
            col_num //= 26
        return result
    
    def _init_google_sheets(self) -> None:
        """Initialize Google Sheets connection."""
        try:
            from ..common.data_exporter import UnifiedDataExporter
            exporter = UnifiedDataExporter(self.output_dir, google_sheets_id=self.google_sheets_id)
            spreadsheet = exporter._get_spreadsheet()
            if spreadsheet:
                # Get or create "Packages Enriched 2" worksheet
                try:
                    self.worksheet = spreadsheet.worksheet("Packages Enriched 2")
                    # Check if worksheet has data
                    existing_data = self.worksheet.get_all_values()
                    
                    # Check if row 1 looks like a header (contains typical header field names)
                    has_header = False
                    if len(existing_data) > 0:
                        first_row = existing_data[0]
                        # Check if first row contains header-like strings (field names)
                        header_keywords = ['package_name', 'deal_ids', 'taxonomy', 'package_id', 'deal_id']
                        has_header = any(
                            isinstance(cell, str) and any(keyword in cell.lower() for keyword in header_keywords)
                            for cell in first_row[:10]  # Check first 10 cells
                        )
                    
                    if len(existing_data) > 1 and has_header:  # Has header + data
                        self.sheets_header_written = True
                        header = existing_data[0]
                        self.sheets_header_columns = len(header)
                        self.sheets_next_row = len(existing_data) + 1
                        logger.info(f"Found existing 'Packages Enriched 2' worksheet with header and {len(existing_data) - 1} data rows")
                    elif len(existing_data) == 1 and has_header:
                        # Has header only
                        self.sheets_header_written = True
                        header = existing_data[0]
                        self.sheets_header_columns = len(header)
                        self.sheets_next_row = 2
                        logger.info("Found 'Packages Enriched 2' worksheet header, will append packages")
                    elif len(existing_data) > 0 and not has_header:
                        # Has data but no header - need to add header
                        self.sheets_header_written = False
                        self.sheets_next_row = len(existing_data) + 1  # Will append after existing data
                        logger.warning(f"Found 'Packages Enriched 2' worksheet with {len(existing_data)} rows but no header - will add header and continue appending")
                    else:
                        # Empty worksheet
                        self.sheets_header_written = False
                        self.sheets_next_row = 2
                        logger.info("Found empty 'Packages Enriched 2' worksheet")
                    
                    # Expand worksheet columns if needed
                    try:
                        current_cols = self.worksheet.col_count
                        cols_needed = max(50, current_cols, 40)  # Enriched packages have many fields
                        
                        if cols_needed > current_cols:
                            self.worksheet.resize(rows=self.worksheet.row_count, cols=cols_needed)
                            logger.info(f"Expanded worksheet columns to {cols_needed}")
                    except Exception as resize_error:
                        logger.warning(f"Could not resize worksheet columns: {resize_error}")
                        
                except Exception:
                    # Create worksheet if it doesn't exist
                    self.worksheet = spreadsheet.add_worksheet(title="Packages Enriched 2", rows=2000, cols=50)
                    logger.info("Created new 'Packages Enriched 2' worksheet")
            else:
                self.worksheet = None
        except Exception as e:
            logger.warning(f"Failed to initialize Google Sheets: {e}")
            self.worksheet = None
    
    def export_package(self, enriched_package: Dict[str, Any]) -> None:
        """
        Export a single enriched package immediately.
        
        Args:
            enriched_package: Enriched package dictionary to export
        """
        # Append to JSON Lines file
        self._append_jsonl(enriched_package)
        
        # Append to JSON array file
        self._append_json(enriched_package)
        
        # Append to Google Sheets
        if self.worksheet:
            self._append_to_sheets(enriched_package)
    
    def _append_jsonl(self, package: Dict[str, Any]) -> None:
        """Append package to JSON Lines file."""
        try:
            with open(self.jsonl_path, 'a', encoding='utf-8') as f:
                json.dump(package, f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            logger.error(f"Failed to append to JSONL file: {e}")
    
    def _append_json(self, package: Dict[str, Any]) -> None:
        """Append package to JSON array file (rewrites entire file)."""
        try:
            packages = []
            
            # Load existing packages if file exists
            if self.json_path.exists():
                try:
                    with open(self.json_path, 'r', encoding='utf-8') as f:
                        packages = json.load(f)
                        if not isinstance(packages, list):
                            packages = []
                except Exception:
                    packages = []
            
            # Add new package
            packages.append(package)
            
            # Write back
            with open(self.json_path, 'w', encoding='utf-8') as f:
                json.dump(packages, f, indent=2, ensure_ascii=False)
            
            self.json_initialized = True
        except Exception as e:
            logger.error(f"Failed to append to JSON file: {e}")
    
    def _append_to_sheets(self, package: Dict[str, Any]) -> None:
        """Append enriched package row to Google Sheets."""
        if not self.worksheet:
            return
        
        try:
            # Flatten package dict
            flattened = flatten_dict(package)
            
            # Create DataFrame with single row
            df_row = pd.DataFrame([flattened])
            
            # Prepare row values (handle NaN, types)
            row_values = []
            for val in df_row.iloc[0]:
                if pd.isna(val):
                    row_values.append(None)
                elif isinstance(val, (np.integer,)):
                    row_values.append(int(val))
                elif isinstance(val, (np.floating,)):
                    row_values.append(float(val))
                elif isinstance(val, (np.bool_,)):
                    row_values.append(bool(val))
                elif isinstance(val, str) and len(val) > 49000:
                    # Truncate long strings
                    row_values.append(val[:49000])
                else:
                    row_values.append(val)
            
            # Check and update header if needed
            if not self.sheets_header_written:
                new_header = df_row.columns.values.tolist()
                try:
                    current_cols = self.worksheet.col_count
                    cols_needed = max(len(new_header) + 10, current_cols, 50)
                    
                    if cols_needed > current_cols:
                        self.worksheet.resize(rows=self.worksheet.row_count, cols=cols_needed)
                        logger.info(f"Expanded worksheet columns to {cols_needed}")
                except Exception as resize_error:
                    logger.warning(f"Could not resize worksheet: {resize_error}")
                
                # Check if there's existing data that needs header inserted
                existing_data = self.worksheet.get_all_values()
                if len(existing_data) > 0:
                    # Header missing but data exists - insert header at row 1
                    logger.warning(f"Header missing but {len(existing_data)} rows exist - inserting header at row 1")
                    try:
                        # Insert header as first row (shifts all existing rows down)
                        self.worksheet.insert_row(new_header, 1)
                        # Update next row to account for inserted header
                        self.sheets_next_row = len(existing_data) + 2
                        logger.info(f"Inserted header, will append at row {self.sheets_next_row}")
                    except Exception as insert_error:
                        logger.error(f"Failed to insert header row: {insert_error}, writing to row 1 (may overwrite data)")
                        self.worksheet.update([new_header], 'A1')
                        self.sheets_next_row = len(existing_data) + 1
                else:
                    # Empty sheet - just write header
                    self.worksheet.update([new_header], 'A1')
                    self.sheets_next_row = 2
                
                logger.info(f"Wrote header with {len(new_header)} columns")
                self.sheets_header_written = True
                self.sheets_header_columns = len(new_header)
            else:
                # Get header column count
                if self.sheets_header_columns:
                    num_cols = self.sheets_header_columns
                else:
                    existing_data = self.worksheet.get_all_values()
                    if len(existing_data) > 0:
                        num_cols = len(existing_data[0])
                        self.sheets_header_columns = num_cols
                    else:
                        num_cols = len(df_row.columns)
                        self.sheets_header_columns = num_cols
            
            # Determine column range
            if self.sheets_header_columns:
                num_cols = self.sheets_header_columns
            else:
                num_cols = len(df_row.columns)
                self.sheets_header_columns = num_cols
            
            # Ensure row_values matches header length
            while len(row_values) < num_cols:
                row_values.append(None)
            
            if len(row_values) > num_cols:
                row_values = row_values[:num_cols]
            
            col_letter_end = self._get_column_letter(num_cols)
            
            # Append new row
            range_name = f'A{self.sheets_next_row}:{col_letter_end}{self.sheets_next_row}'
            self.worksheet.update([row_values], range_name)
            logger.debug(f"Appended enriched package to Google Sheets (row {self.sheets_next_row}, {num_cols} cols)")
            self.sheets_next_row += 1
            
        except Exception as e:
            logger.error(f"Failed to append to Google Sheets: {e}")
            # Don't fail the entire process if Sheets append fails
    
    def finalize(self) -> dict:
        """
        Finalize export and return file paths.
        
        Returns:
            Dictionary with file paths
        """
        return {
            'jsonl': self.jsonl_path,
            'json': self.json_path
        }
