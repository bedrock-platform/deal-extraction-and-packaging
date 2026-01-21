"""
Incremental Exporter for Row-by-Row Enrichment Persistence

Saves enriched deals immediately after enrichment and appends to Google Sheets.
"""
import json
import logging
from pathlib import Path
from typing import List, Optional
import pandas as pd
import numpy as np

from ..common.schema import EnrichedDeal
from ..common.data_exporter import flatten_dict

logger = logging.getLogger(__name__)


class IncrementalExporter:
    """
    Exports enriched deals incrementally (row-by-row) to files and Google Sheets.
    
    Features:
    - Appends to JSON Lines file (one JSON object per line)
    - Appends to TSV file (with header on first write)
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
        self.jsonl_path = output_dir / f"deals_enriched_{timestamp}.jsonl"
        self.tsv_path = output_dir / f"deals_enriched_{timestamp}.tsv"
        
        # Track if TSV header has been written
        # Check if files already exist (resume mode)
        self.tsv_header_written = self.tsv_path.exists()
        if self.tsv_header_written:
            # Read existing TSV to get column order
            try:
                df_existing = pd.read_csv(self.tsv_path, sep='\t', nrows=0)
                self.tsv_columns = list(df_existing.columns)
                logger.info(f"Resuming: TSV file exists with {len(self.tsv_columns)} columns")
            except Exception as e:
                logger.warning(f"Failed to read existing TSV header: {e}")
                self.tsv_header_written = False
                self.tsv_columns = None
        else:
            self.tsv_columns = None
        
        # Initialize deal_id_to_row mapping (will be populated in _init_google_sheets)
        self.deal_id_to_row = {}
        
        # Google Sheets
        self.google_sheets_id = google_sheets_id
        self.worksheet = None
        self.sheets_header_written = False
        self.sheets_header_updated = False  # Track if we've updated header with enrichment columns
        self.sheets_header_columns = None  # Store actual header column count after update
        self.sheets_next_row = 2  # Row 1 is header
        self.deal_id_to_row = {}  # Map deal_id to row number for updating existing rows
        
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
                # Get or create "Unified" worksheet
                try:
                    self.worksheet = spreadsheet.worksheet("Unified")
                    # Check if worksheet has data
                    existing_data = self.worksheet.get_all_values()
                    if len(existing_data) > 1:  # Has header + data
                        self.sheets_header_written = True
                        # Build deal_id to row number mapping for updating existing rows
                        self.deal_id_to_row = {}
                        if len(existing_data) > 0:
                            header = existing_data[0]
                            self.sheets_header_columns = len(header)  # Store header column count
                            deal_id_col_idx = None
                            for idx, col_name in enumerate(header):
                                if col_name.lower() == 'deal_id':
                                    deal_id_col_idx = idx
                                    break
                            
                            if deal_id_col_idx is not None:
                                for row_idx, row_data in enumerate(existing_data[1:], start=2):  # Start at row 2 (row 1 is header)
                                    if len(row_data) > deal_id_col_idx and row_data[deal_id_col_idx]:
                                        deal_id = str(row_data[deal_id_col_idx]).strip()
                                        if deal_id:
                                            self.deal_id_to_row[deal_id] = row_idx
                                logger.info(f"Found {len(self.deal_id_to_row)} existing rows to update with enrichment data")
                            else:
                                logger.warning("Could not find 'deal_id' column in existing data, will append instead")
                        self.sheets_next_row = len(existing_data) + 1  # Fallback for appending if deal_id not found
                    elif len(existing_data) == 1:
                        # Has header only (pre-enrichment data was just uploaded)
                        self.sheets_header_written = True
                        self.sheets_next_row = 2
                        self.deal_id_to_row = {}
                        header = existing_data[0]
                        self.sheets_header_columns = len(header)  # Store header column count
                        logger.info("Found Google Sheets header (pre-enrichment data uploaded), will update existing rows with enrichment")
                    
                    # Expand worksheet columns if needed for enrichment columns
                    try:
                        current_cols = self.worksheet.col_count
                        cols_needed = max(50, current_cols, 40)  # Enriched data has ~33 columns, add buffer
                        
                        if cols_needed > current_cols:
                            self.worksheet.resize(rows=self.worksheet.row_count, cols=cols_needed)
                            logger.info(f"Expanded worksheet columns to {cols_needed} for enrichment columns")
                    except Exception as resize_error:
                        logger.warning(f"Could not resize worksheet columns: {resize_error}")
                        
                except Exception:
                    # Create worksheet if it doesn't exist
                    self.worksheet = spreadsheet.add_worksheet(title="Unified", rows=2000, cols=50)
                    logger.info("Created new 'Unified' worksheet")
                    self.deal_id_to_row = {}
            else:
                self.worksheet = None
                self.deal_id_to_row = {}
        except Exception as e:
            logger.warning(f"Failed to initialize Google Sheets: {e}")
            self.worksheet = None
            self.deal_id_to_row = {}
    
    def export_deal(self, enriched_deal: EnrichedDeal) -> None:
        """
        Export a single enriched deal immediately.
        
        Args:
            enriched_deal: EnrichedDeal instance to export
        """
        deal_dict = enriched_deal.model_dump(mode='json')
        
        # Append to JSON Lines file
        self._append_jsonl(deal_dict)
        
        # Append to TSV file
        self._append_tsv(deal_dict)
        
        # Append to Google Sheets
        if self.worksheet:
            self._append_to_sheets(deal_dict)
    
    def _append_jsonl(self, deal_dict: dict) -> None:
        """Append deal to JSON Lines file."""
        try:
            with open(self.jsonl_path, 'a', encoding='utf-8') as f:
                json.dump(deal_dict, f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            logger.error(f"Failed to append to JSONL file: {e}")
    
    def _append_tsv(self, deal_dict: dict) -> None:
        """Append deal to TSV file."""
        try:
            # Flatten deal dict
            flattened = flatten_dict(deal_dict, exclude_keys={'raw_deal_data'})
            
            # Ensure raw_deal_data is present as JSON string
            if 'raw_deal_data' not in flattened:
                flattened['raw_deal_data'] = json.dumps(deal_dict.get('raw_deal_data', {}))
            
            # Create DataFrame with single row
            df_row = pd.DataFrame([flattened])
            
            # Write header if first time
            if not self.tsv_header_written:
                df_row.to_csv(self.tsv_path, index=False, sep='\t', mode='w')
                self.tsv_header_written = True
                self.tsv_columns = list(df_row.columns)
            else:
                # Append row (ensure column order matches)
                if self.tsv_columns:
                    # Reorder columns to match header
                    df_row = df_row.reindex(columns=self.tsv_columns, fill_value=None)
                df_row.to_csv(self.tsv_path, index=False, sep='\t', mode='a', header=False)
        except Exception as e:
            logger.error(f"Failed to append to TSV file: {e}")
    
    def _append_to_sheets(self, deal_dict: dict) -> None:
        """Append deal row to Google Sheets."""
        if not self.worksheet:
            return
        
        try:
            # Flatten deal dict
            flattened = flatten_dict(deal_dict, exclude_keys={'raw_deal_data'})
            
            # Ensure raw_deal_data is present as JSON string
            if 'raw_deal_data' not in flattened:
                flattened['raw_deal_data'] = json.dumps(deal_dict.get('raw_deal_data', {}))
            
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
            
            # Check and update header if needed (for enrichment columns)
            if not self.sheets_header_updated:
                # Get current header from worksheet
                existing_data = self.worksheet.get_all_values()
                new_header = df_row.columns.values.tolist()
                
                if len(existing_data) > 0:
                    # Header exists, check if columns match
                    existing_header = existing_data[0]
                    
                    if existing_header != new_header:
                        # Headers don't match (pre-enrichment has fewer columns)
                        # Update header to include enrichment columns
                        # Expand columns if needed
                        try:
                            current_cols = self.worksheet.col_count
                            cols_needed = max(len(new_header) + 10, current_cols, 50)
                            
                            if cols_needed > current_cols:
                                self.worksheet.resize(rows=self.worksheet.row_count, cols=cols_needed)
                                logger.info(f"Expanded worksheet columns to {cols_needed} for enrichment columns")
                        except Exception as resize_error:
                            logger.warning(f"Could not resize worksheet: {resize_error}")
                        
                        self.worksheet.update([new_header], 'A1')
                        logger.info(f"Updated header with enrichment columns ({len(new_header)} cols)")
                        self.sheets_header_updated = True
                        self.sheets_header_columns = len(new_header)  # Store header column count
                elif not self.sheets_header_written:
                    # No existing header, write it for the first time
                    try:
                        current_cols = self.worksheet.col_count
                        cols_needed = max(len(new_header) + 10, current_cols, 50)
                        
                        if cols_needed > current_cols:
                            self.worksheet.resize(rows=self.worksheet.row_count, cols=cols_needed)
                            logger.info(f"Expanded worksheet columns to {cols_needed} for enrichment columns")
                    except Exception as resize_error:
                        logger.warning(f"Could not resize worksheet: {resize_error}")
                    
                    self.worksheet.update([new_header], 'A1')
                    logger.info(f"Wrote header with enrichment columns ({len(new_header)} cols)")
                    self.sheets_header_written = True
                    self.sheets_header_updated = True
                    self.sheets_header_columns = len(new_header)  # Store header column count
            
            # Determine actual header column count (use stored value or get from worksheet)
            if self.sheets_header_columns:
                num_cols = self.sheets_header_columns
            else:
                # Fallback: get from worksheet header
                existing_data = self.worksheet.get_all_values()
                if len(existing_data) > 0:
                    num_cols = len(existing_data[0])
                else:
                    num_cols = len(df_row.columns)
                    # Store it for future use
                    self.sheets_header_columns = num_cols
            
            # Ensure row_values matches header length (pad with None if needed)
            while len(row_values) < num_cols:
                row_values.append(None)
            
            # Truncate if somehow longer (shouldn't happen, but safety check)
            if len(row_values) > num_cols:
                row_values = row_values[:num_cols]
                logger.warning(f"Row values truncated from {len(row_values)} to {num_cols} columns")
            
            # Update existing row or append if not found
            deal_id = deal_dict.get('deal_id')
            target_row = None
            
            if deal_id and self.deal_id_to_row:
                target_row = self.deal_id_to_row.get(str(deal_id))
            
            col_letter_end = self._get_column_letter(num_cols)
            
            if target_row:
                # Update existing row with enrichment data (full column range)
                range_name = f'A{target_row}:{col_letter_end}{target_row}'
                self.worksheet.update([row_values], range_name)
                logger.debug(f"Updated deal {deal_id} in Google Sheets (row {target_row}, {num_cols} cols)")
            else:
                # Append new row if deal_id not found in existing data
                range_name = f'A{self.sheets_next_row}:{col_letter_end}{self.sheets_next_row}'
                self.worksheet.update([row_values], range_name)
                logger.debug(f"Appended deal {deal_id} to Google Sheets (row {self.sheets_next_row}, {num_cols} cols)")
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
            'tsv': self.tsv_path
        }
