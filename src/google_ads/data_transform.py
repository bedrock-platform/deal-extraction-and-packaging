"""
Data transformation module for Google Authorized Buyers inventory data.

Contains helper functions for transforming raw API data into exportable formats.
"""

import json
from typing import Dict, List


def get_top_breakdown_slice(breakdowns_list, filter_type, total_impressions):
    """Get top slice from breakdown with name, impressions, and percentage."""
    for breakdown in breakdowns_list:
        if breakdown.get("filterType") == filter_type:
            slices = breakdown.get("slices", [])
            if slices:
                sorted_slices = sorted(
                    slices,
                    key=lambda x: int(x.get("impressions", 0)),
                    reverse=True
                )
                top_slice = sorted_slices[0]
                top_impressions = int(top_slice.get("impressions", 0))
                percentage = (top_impressions / total_impressions * 100) if total_impressions > 0 else 0
                return {
                    "name": top_slice.get("name", ""),
                    "impressions": str(top_impressions),
                    "percentage": f"{percentage:.1f}"
                }
    return {"name": "", "impressions": "", "percentage": ""}


def extract_package_details(entity_id: str, package_details: Dict[str, Dict]) -> Dict:
    """
    Extract package details (email, floor price, created by) from hydrated data.
    
    Args:
        entity_id: Entity ID to extract details for
        package_details: Dictionary mapping entity_id -> detail data
        
    Returns:
        Dictionary with extracted fields
    """
    detail = package_details.get(entity_id, {})
    seller_contacts = detail.get("sellerContacts", [])
    email_contact = seller_contacts[0] if seller_contacts else ""
    created_by = detail.get("publisherSummary", {}).get("displayName", "")
    
    # Extract floor price from priorityFloorPrice
    floor_price = ""
    floor_price_obj = detail.get("priorityFloorPrice", {})
    if floor_price_obj:
        if "units" in floor_price_obj:
            units = floor_price_obj.get("units", "")
            nanos = floor_price_obj.get("nanos", 0)
            if units or nanos:
                # Convert nanos to decimal (nanos are in micros, so divide by 1,000,000)
                total_price = float(units) + (float(nanos) / 1000000) if nanos else float(units)
                floor_price = f"{total_price:.2f}"
        elif "nanos" in floor_price_obj:
            nanos = floor_price_obj.get("nanos", 0)
            if nanos:
                floor_price = f"{nanos / 1000000:.2f}"
    
    return {
        "email_contact": email_contact,
        "created_by": created_by,
        "floor_price": floor_price
    }


def extract_publisher_info(entity: Dict, detail: Dict) -> Dict:
    """
    Extract publisher information from entity or detail.
    
    Args:
        entity: Entity dictionary
        detail: Hydrated detail dictionary
        
    Returns:
        Dictionary with publisher fields
    """
    publisher = ""
    publisher_account_id = ""
    publisher_logo_url = ""
    publisher_summaries = entity.get("publisherSummaries", [])
    if publisher_summaries and isinstance(publisher_summaries, list):
        if len(publisher_summaries) > 0:
            publisher = publisher_summaries[0].get("displayName", "").strip()
            publisher_account_id = publisher_summaries[0].get("accountId", "")
            publisher_logo_url = publisher_summaries[0].get("logoUrl", "")
    elif detail.get("publisherSummary"):
        # Fallback to hydrated detail if not in entity
        pub_summary = detail.get("publisherSummary", {})
        publisher = pub_summary.get("displayName", "").strip()
        publisher_account_id = pub_summary.get("accountId", "")
        publisher_logo_url = pub_summary.get("logoUrl", "")
    
    return {
        "publisher": publisher,
        "publisher_account_id": publisher_account_id,
        "publisher_logo_url": publisher_logo_url
    }


def calculate_cpm_metrics(cost_histogram: List[Dict]) -> Dict[str, str]:
    """
    Calculate CPM metrics from cost histogram.
    
    Args:
        cost_histogram: List of cost histogram buckets
        
    Returns:
        Dictionary with CPM metrics (avg, min, max, median)
    """
    avg_cpm = ""
    min_cpm = ""
    max_cpm = ""
    median_cpm = ""
    
    if cost_histogram and isinstance(cost_histogram, list):
        cpm_values = []
        cpm_impressions_pairs = []  # For weighted calculations
        total_weighted_cpm = 0
        total_impressions = 0
        
        for bucket in cost_histogram:
            impressions = int(bucket.get("impressions", 0))
            cpm_micros = int(bucket.get("cpmUsdMicros", 0))
            cpm_usd = cpm_micros / 1000000  # Convert micros to USD
            
            if impressions > 0:
                cpm_values.append(cpm_usd)
                cpm_impressions_pairs.append((cpm_usd, impressions))
                total_weighted_cpm += cpm_usd * impressions
                total_impressions += impressions
        
        if cpm_values:
            min_cpm = f"{min(cpm_values):.2f}"
            max_cpm = f"{max(cpm_values):.2f}"
            if total_impressions > 0:
                avg_cpm = f"{total_weighted_cpm / total_impressions:.2f}"
            
            # Calculate median CPM
            sorted_cpm = sorted(cpm_values)
            n = len(sorted_cpm)
            if n > 0:
                if n % 2 == 0:
                    median_cpm = f"{(sorted_cpm[n//2 - 1] + sorted_cpm[n//2]) / 2:.2f}"
                else:
                    median_cpm = f"{sorted_cpm[n//2]:.2f}"
    
    return {
        "avg_cpm": avg_cpm,
        "min_cpm": min_cpm,
        "max_cpm": max_cpm,
        "median_cpm": median_cpm
    }


def build_breakdown_json(breakdowns: List[Dict]) -> Dict[str, str]:
    """
    Build nested JSON breakdowns for all filter types.
    
    Args:
        breakdowns: List of breakdown dictionaries
        
    Returns:
        Dictionary mapping column names to JSON strings
    """
    breakdown_json = {}
    for breakdown in breakdowns:
        filter_type = breakdown.get("filterType")
        slices = breakdown.get("slices", [])
        if slices:
            # Create dictionary: {slice_name: impressions}
            nested_data = {
                slice_data.get("name", ""): slice_data.get("impressions", "0")
                for slice_data in slices
                if slice_data.get("name", "")
            }
            if nested_data:
                # Map filter types to readable column names
                column_name_map = {
                    "REQUEST_FORMAT": "Request_Format_Breakdown",
                    "GENDER": "Gender_Breakdown",
                    "AGE": "Age_Breakdown",
                    "DEVICE": "Device_Breakdown",
                    "COUNTRY": "Country_Breakdown",
                    "INVENTORY_SIZE": "Inventory_Size_Breakdown",
                    "CONTENT_VERTICAL": "Content_Vertical_Breakdown",
                    "VIDEO_DURATION": "Video_Duration_Breakdown",
                    "DOMAIN_NAME": "Domain_Name_Breakdown",
                    "MOBILE_APP_ID": "App_ID_Breakdown"
                }
                column_name = column_name_map.get(filter_type, f"{filter_type}_Breakdown")
                breakdown_json[column_name] = json.dumps(nested_data)
    
    # Initialize all JSON columns (empty JSON object if breakdown doesn't exist)
    json_columns = {
        "Request_Format_Breakdown": "{}",
        "Gender_Breakdown": "{}",
        "Age_Breakdown": "{}",
        "Device_Breakdown": "{}",
        "Country_Breakdown": "{}",
        "Inventory_Size_Breakdown": "{}",
        "Content_Vertical_Breakdown": "{}",
        "Video_Duration_Breakdown": "{}",
        "Domain_Name_Breakdown": "{}",
        "App_ID_Breakdown": "{}"
    }
    json_columns.update(breakdown_json)
    
    return json_columns
