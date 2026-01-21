"""
Data export module for Google Authorized Buyers inventory data.

Handles JSON and TSV/CSV export with data transformation.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

from .data_transform import (
    build_breakdown_json,
    calculate_cpm_metrics,
    extract_package_details,
    extract_publisher_info,
    get_top_breakdown_slice,
)

logger = logging.getLogger(__name__)


class DataExporter:
    """Handles export of inventory data to various formats."""
    
    def __init__(self, output_dir: Path):
        """
        Initialize data exporter.
        
        Args:
            output_dir: Directory where output files will be saved
        """
        self.output_dir = output_dir
        self.output_dir.mkdir(exist_ok=True)
    
    def save_json(self, entities: List[Dict], timestamp: Optional[str] = None) -> Path:
        """
        Save entities to JSON file with timestamp.

        Args:
            entities: List of entity dictionaries
            timestamp: Optional ISO 8601 timestamp string (generated if not provided)

        Returns:
            Path to the saved JSON file
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")

        filename = f"inventory_{timestamp}.json"
        filepath = self.output_dir / filename

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(entities, f, indent=2, ensure_ascii=False)

        logger.info(f"Saved JSON file: {filepath}")
        return filepath
    
    def export_to_csv(
        self,
        entities: List[Dict],
        package_details: Dict[str, Dict],
        timestamp: Optional[str] = None
    ) -> Dict[str, Path]:
        """
        Export entities to a single comprehensive TSV file with all slice data flattened into columns.
        Also hydrates package details (email, floor price, created by) via parallel API calls.

        Args:
            entities: List of entity dictionaries
            package_details: Dictionary mapping entity_id -> hydrated detail data
            timestamp: Optional ISO 8601 timestamp string (generated if not provided)

        Returns:
            Dictionary mapping file type to file path
        """
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")

        output_files = {}
        
        # STEP 1: Build comprehensive rows with hybrid schema (flat primary metrics + nested JSON breakdowns)
        summary_rows = []
        for entity in entities:
            entity_id = entity.get("entityId", "")
            forecast = entity.get("forecast", {})
            metrics = forecast.get("metrics", {})
            total_metrics = forecast.get("totalMetrics", {})
            breakdowns = forecast.get("breakdowns", [])
            
            # Calculate total impressions for percentage calculations
            total_impressions = int(metrics.get("impressions", 0))
            
            # Extract hydrated package details
            detail = package_details.get(entity_id, {})
            pkg_details = extract_package_details(entity_id, package_details)
            pub_info = extract_publisher_info(entity, detail)
            
            # Entity category
            entity_category_raw = entity.get("entityCategory", "")
            entity_category = entity_category_raw.replace("_", " ").title()
            
            # Clean up marketplace package type (remove MARKETPLACE_PACKAGE_TYPE_ prefix)
            package_type_raw = entity.get("marketplacePackageType", "")
            package_type = package_type_raw.replace("MARKETPLACE_PACKAGE_TYPE_", "").replace("_", " ").title()
            if not package_type:
                package_type = "Public"  # Default
            
            # Get content type and clean it up
            content_type_raw = forecast.get("contentType", "")
            if content_type_raw:
                # Remove CONTENT_TYPE_ prefix and format nicely
                content_type = content_type_raw.replace("CONTENT_TYPE_", "").replace("_", " ").title()
            else:
                content_type = "Other"  # Default based on UI
            
            # Calculate CPM pricing from costHistogramMetrics
            cost_histogram = entity.get("costHistogramMetrics", [])
            cpm_metrics = calculate_cpm_metrics(cost_histogram)
            
            # Extract top breakdown slices (for flat "Primary" columns - only #1 value for filtering)
            device_top = get_top_breakdown_slice(breakdowns, "DEVICE", total_impressions)
            request_format_top = get_top_breakdown_slice(breakdowns, "REQUEST_FORMAT", total_impressions)
            content_vertical_top = get_top_breakdown_slice(breakdowns, "CONTENT_VERTICAL", total_impressions)
            video_duration_top = get_top_breakdown_slice(breakdowns, "VIDEO_DURATION", total_impressions)
            gender_top = get_top_breakdown_slice(breakdowns, "GENDER", total_impressions)
            age_top = get_top_breakdown_slice(breakdowns, "AGE", total_impressions)
            country_top = get_top_breakdown_slice(breakdowns, "COUNTRY", total_impressions)
            inventory_size_top = get_top_breakdown_slice(breakdowns, "INVENTORY_SIZE", total_impressions)
            domain_name_top = get_top_breakdown_slice(breakdowns, "DOMAIN_NAME", total_impressions)
            mobile_app_id_top = get_top_breakdown_slice(breakdowns, "MOBILE_APP_ID", total_impressions)
            
            # Build nested JSON breakdowns (for high-cardinality categories)
            json_columns = build_breakdown_json(breakdowns)
            
            summary_rows.append({
                # Basic entity fields
                "Name": entity.get("entityName", ""),
                "ID": entity.get("entityId", ""),
                "Entity Category": entity_category,
                "Description": entity.get("description", ""),
                
                # Publisher fields
                "Publisher": pub_info["publisher"],
                "Publisher Account ID": pub_info["publisher_account_id"],
                
                # Package metadata (including hydrated fields)
                "Package Type": package_type,
                "Content Type": content_type,
                "Created By": pkg_details["created_by"],
                "Floor Price (USD)": pkg_details["floor_price"],
                
                # Metrics (filtered)
                "Impressions": metrics.get("impressions", "0"),
                "Uniques": metrics.get("uniqueUsers", "0"),
                
                # Metrics (total)
                "Total Impressions": total_metrics.get("impressions", metrics.get("impressions", "0")),
                "Total Uniques": total_metrics.get("uniqueUsers", metrics.get("uniqueUsers", "0")),
                
                # CPM pricing
                "Avg CPM (USD)": cpm_metrics["avg_cpm"],
                "Min CPM (USD)": cpm_metrics["min_cpm"],
                "Max CPM (USD)": cpm_metrics["max_cpm"],
                "Median CPM (USD)": cpm_metrics["median_cpm"],
                
                # DEVICE breakdown (Primary only - full breakdown in Device_Breakdown JSON)
                "Primary Device": device_top.get("name", ""),
                "Primary Device Impressions": device_top.get("impressions", ""),
                "Primary Device %": device_top.get("percentage", ""),
                
                # REQUEST_FORMAT breakdown (Primary only - full breakdown in Request_Format_Breakdown JSON)
                "Primary Request Format": request_format_top.get("name", ""),
                "Primary Request Format Impressions": request_format_top.get("impressions", ""),
                "Primary Request Format %": request_format_top.get("percentage", ""),
                
                # CONTENT_VERTICAL breakdown (Primary only - full breakdown in Content_Vertical_Breakdown JSON)
                "Primary Content Vertical": content_vertical_top.get("name", ""),
                "Primary Content Vertical Impressions": content_vertical_top.get("impressions", ""),
                "Primary Content Vertical %": content_vertical_top.get("percentage", ""),
                
                # VIDEO_DURATION breakdown
                "Primary Video Duration": video_duration_top.get("name", ""),
                "Primary Video Duration Impressions": video_duration_top.get("impressions", ""),
                "Primary Video Duration %": video_duration_top.get("percentage", ""),
                
                # GENDER breakdown
                "Primary Gender": gender_top.get("name", ""),
                "Primary Gender Impressions": gender_top.get("impressions", ""),
                "Primary Gender %": gender_top.get("percentage", ""),
                
                # AGE breakdown
                "Primary Age Range": age_top.get("name", ""),
                "Primary Age Range Impressions": age_top.get("impressions", ""),
                "Primary Age Range %": age_top.get("percentage", ""),
                
                # COUNTRY breakdown
                "Primary Country": country_top.get("name", ""),
                "Primary Country Impressions": country_top.get("impressions", ""),
                "Primary Country %": country_top.get("percentage", ""),
                
                # INVENTORY_SIZE breakdown (Primary only)
                "Primary Ad Size": inventory_size_top.get("name", ""),
                "Primary Ad Size Impressions": inventory_size_top.get("impressions", ""),
                "Primary Ad Size %": inventory_size_top.get("percentage", ""),
                
                # DOMAIN_NAME breakdown (Primary only)
                "Primary Domain": domain_name_top.get("name", ""),
                "Primary Domain Impressions": domain_name_top.get("impressions", ""),
                "Primary Domain %": domain_name_top.get("percentage", ""),
                
                # MOBILE_APP_ID breakdown (Primary only)
                "Primary App": mobile_app_id_top.get("name", ""),
                "Primary App Impressions": mobile_app_id_top.get("impressions", ""),
                "Primary App %": mobile_app_id_top.get("percentage", ""),
                
                # Nested JSON breakdowns (all slices as JSON strings)
                **json_columns
            })

        if summary_rows:
            df_summary = pd.DataFrame(summary_rows)
            output_path = self.output_dir / f"inventory_{timestamp}.tsv"
            df_summary.to_csv(output_path, index=False, sep='\t')
            output_files["tsv"] = output_path
            logger.info(f"Saved comprehensive TSV: {output_path} ({len(summary_rows)} rows, {len(df_summary.columns)} columns)")

        return output_files
    
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
        if timestamp is None:
            timestamp = datetime.now().strftime("%Y-%m-%dT%H%M")
        
        output_files = {}
        
        rows = []
        for pkg_data in packages:
            auction_pkg = pkg_data.get("auctionPackage", {})
            forecast_metrics = pkg_data.get("forecastMetrics", {})
            targeting = auction_pkg.get("targeting", [])
            
            # Extract targeting criteria into readable format
            targeting_dict = {}
            for target in targeting:
                target_type = target.get("targetingType", "")
                # Clean up target type name
                target_name = target_type.replace("TARGETING_TYPE_", "").replace("_", " ").title()
                values = target.get("includedValues", [])
                value_names = [v.get("displayName", v.get("id", "")) for v in values]
                targeting_dict[target_name] = ", ".join(value_names)
            
            # Extract created by info
            created_by = auction_pkg.get("createdBy", {})
            created_by_name = created_by.get("displayName", "")
            
            rows.append({
                "Name": auction_pkg.get("name", ""),
                "ID": auction_pkg.get("externalDealId", ""),
                "Description": auction_pkg.get("description", ""),
                "Created By": created_by_name,
                "Status": auction_pkg.get("status", ""),
                "Content Type": pkg_data.get("contentType", "").replace("CONTENT_TYPE_", "").replace("_", " ").title(),
                "Impressions": forecast_metrics.get("impressions", "0"),
                "Uniques": forecast_metrics.get("uniqueUsers", "0"),
                "Creation Time": auction_pkg.get("creationTime", ""),
                "Update Time": auction_pkg.get("updateTime", ""),
                # Targeting fields (flatten common ones)
                "Targeting - Country": targeting_dict.get("Country", ""),
                "Targeting - Content Vertical": targeting_dict.get("Content Vertical", ""),
                "Targeting - Content Language": targeting_dict.get("Content Language", ""),
                "Targeting - Seller Status": targeting_dict.get("Authorized Seller Status", ""),
                "Targeting - Viewability": targeting_dict.get("Viewability", ""),
                # Full targeting as JSON
                "Targeting_JSON": json.dumps(targeting_dict)
            })
        
        if rows:
            df = pd.DataFrame(rows)
            output_path = self.output_dir / f"google_curated_{timestamp}.tsv"
            df.to_csv(output_path, index=False, sep='\t')
            output_files["tsv"] = output_path
            logger.info(f"Saved Google Curated TSV: {output_path} ({len(rows)} rows, {len(df.columns)} columns)")

        return output_files
