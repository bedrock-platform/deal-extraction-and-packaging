"""
API client for Google Authorized Buyers internal API.

Handles API requests, pagination, and error handling.
"""

import json
import logging
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional

import requests

from .auth import AuthManager

logger = logging.getLogger(__name__)


class APIClient:
    """Client for making API requests to Google Authorized Buyers."""
    
    def __init__(self, account_id: str, api_key: str, auth_manager: AuthManager):
        """
        Initialize API client.
        
        Args:
            account_id: Google Authorized Buyers account ID
            api_key: API key for authentication
            auth_manager: AuthManager instance for authentication
        """
        self.account_id = account_id
        self.api_key = api_key
        self.auth_manager = auth_manager
        
        # Build API URL (matching browser format with double slash)
        self.base_url = (
            f"https://adexchangebuyer.clients6.google.com//v1internal/"
            f"accounts/{self.account_id}/inventoryViews:search"
            f"?key={self.api_key}"
        )
    
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

        Raises:
            requests.exceptions.HTTPError: If API request fails
            ValueError: If bearer token is expired (401 error)
        """
        if payload is None:
            # Default payload matching the browser's request structure
            payload = {
                "pageSize": "20",
                "continuationToken": "",
                "sortOrder": "FILTERED_IMPRESSIONS",
                "breakdownCategories": [
                    "REQUEST_FORMAT", "GENDER", "COUNTRY", "DEVICE", "AGE",
                    "VIDEO_DURATION", "CONTENT_VERTICAL",
                    "DOMAIN_NAME",    # Top sites (yahoo.com, mail.yahoo.com, etc.)
                    "MOBILE_APP_ID",  # Top apps (mobile app names/IDs)
                    "INVENTORY_SIZE"  # Ad sizes (300x250, 320x50, etc.)
                ],
                "costHistogramResolution": 100,
                "currencyCode": "USD",
                "entityCategories": ["MARKETPLACE_PACKAGE"],
                "filters": [],
                "maxBreakdownSlices": 20
            }
            logger.info("Using default payload matching browser structure.")

        all_entities = []
        next_token = None
        page_count = 1

        logger.info("Starting inventory data fetch...")

        while True:
            logger.info(f"Fetching page {page_count}...")

            # Add continuation token if we have one
            current_payload = payload.copy()
            if next_token:
                current_payload["continuationToken"] = next_token
            else:
                # Clear continuationToken for first page
                current_payload["continuationToken"] = ""

            # Get fresh headers with valid token
            headers = self.auth_manager.get_authenticated_headers()

            # Make API request
            logger.debug(f"Request URL: {self.base_url}")
            logger.debug(f"Request headers: {json.dumps(dict(headers), indent=2)}")
            logger.debug(f"Request payload: {json.dumps(current_payload, indent=2)}")

            try:
                # For SAPISIDHASH, cookies are sent as Cookie header (already in headers)
                # Don't use cookies parameter to avoid duplication
                response = requests.post(
                    self.base_url,
                    headers=headers,
                    json=current_payload,
                    timeout=30
                )

                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {dict(response.headers)}")

                # Handle 400 Bad Request
                if response.status_code == 400:
                    try:
                        error_data = response.json()
                        error_message = error_data.get("error", {}).get("message", "")
                        logger.error(f"400 Bad Request: {error_message}")
                    except (json.JSONDecodeError, KeyError):
                        pass

                # Handle token expiration
                if response.status_code == 401:
                    try:
                        error_body = response.text[:500]  # First 500 chars of error
                        logger.debug(f"Error response body: {error_body}")
                    except:
                        pass
                    
                    if self.auth_manager.auth_method == "SAPISIDHASH":
                        error_msg = (
                            "SAPISIDHASH authentication failed. Update AUTHORIZED_BUYERS_SAPISIDHASH "
                            "and AUTHORIZED_BUYERS_COOKIES in your .env file with fresh values from Chrome DevTools. "
                            f"Response: {response.text[:200] if response.text else 'No response body'}"
                        )
                        logger.error(error_msg)
                        raise ValueError(error_msg)
                    else:
                        error_msg = (
                            "Bearer token expired. Update AUTHORIZED_BUYERS_BEARER_TOKEN "
                            "in your .env file with a fresh token from Chrome DevTools."
                        )
                    logger.error(error_msg)
                    raise ValueError(error_msg)

                # Handle 403 errors
                if response.status_code == 403:
                    try:
                        error_data = response.json()
                        error_message = error_data.get("error", {}).get("message", "")
                        logger.error(f"403 Forbidden: {error_message}")
                        raise ValueError(
                            f"403 Forbidden - Access Denied\n\n"
                            f"Error: {error_message}\n\n"
                            f"Possible causes:\n"
                            f"1. Tokens expired - Update AUTHORIZED_BUYERS_SAPISIDHASH and AUTHORIZED_BUYERS_COOKIES\n"
                            f"2. Invalid API key - Verify AUTHORIZED_BUYERS_API_KEY is correct\n"
                            f"3. Account permissions - Verify account has access to Authorized Buyers"
                        )
                    except (json.JSONDecodeError, KeyError):
                        raise ValueError("403 Forbidden - Access denied. Check your authentication tokens.")

                # Log error details for debugging
                if response.status_code >= 400:
                    try:
                        error_body = response.text[:1000]  # First 1000 chars
                        logger.debug(f"Error response body: {error_body}")
                        logger.error(f"HTTP {response.status_code} error: {error_body[:200]}")
                    except:
                        pass
                
                # Raise exception for other HTTP errors
                response.raise_for_status()

                # Parse response
                data = response.json()
                logger.debug(f"Response data keys: {data.keys()}")

                # Extract entities from current page
                entities = data.get("entities", [])
                all_entities.extend(entities)
                logger.info(f"Page {page_count}: Found {len(entities)} entities (Total: {len(all_entities)})")

                # Check for next page
                next_token = data.get("continuationToken")

                if not next_token:
                    logger.info("No more pages found. Fetch complete.")
                    break

                page_count += 1
                time.sleep(rate_limit_delay)

            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed: {e}")
                raise

        logger.info(f"Successfully fetched {len(all_entities)} total entities across {page_count} pages.")
        return all_entities
    
    def hydrate_package_details(self, entity_ids: List[str]) -> Dict[str, Dict]:
        """
        Fetch package details (email, floor price, created by) for multiple entities.
        Uses threading for parallel requests with backoff to avoid rate limits.
        
        Args:
            entity_ids: List of entity IDs to fetch details for
            
        Returns:
            Dictionary mapping entity_id -> detail data
        """
        if not entity_ids:
            return {}
        
        details = {}
        
        def fetch_single_detail(entity_id: str) -> tuple:
            """Fetch detail for a single entity."""
            url = (
                f"https://adexchangebuyer.clients6.google.com"
                f"//v1internal/buyers/{self.account_id}/marketplacePackages/{entity_id}"
            )
            params = {"key": self.api_key}
            headers = self.auth_manager.get_authenticated_headers()
            
            try:
                time.sleep(0.2)  # Backoff to avoid rate limits
                response = requests.get(url, params=params, headers=headers)
                response.raise_for_status()
                return (entity_id, response.json())
            except Exception as e:
                logger.warning(f"Failed to fetch details for {entity_id}: {e}")
                return (entity_id, None)
        
        # Use ThreadPoolExecutor for parallel requests (5 workers to avoid rate limits)
        logger.info(f"Fetching package details for {len(entity_ids)} entities...")
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {executor.submit(fetch_single_detail, eid): eid for eid in entity_ids}
            
            completed = 0
            for future in as_completed(futures):
                entity_id, detail_data = future.result()
                completed += 1
                if detail_data:
                    details[entity_id] = detail_data
                if completed % 50 == 0:
                    logger.info(f"Fetched details for {completed}/{len(entity_ids)} packages...")
        
        logger.info(f"Successfully fetched details for {len(details)}/{len(entity_ids)} packages")
        return details
    
    def fetch_google_curated_packages(self, page_size: int = 20) -> List[Dict]:
        """
        Fetch all Google Curated packages with pagination support.
        
        Args:
            page_size: Number of packages per page
            
        Returns:
            List of all Google Curated packages across all pages
        """
        url = (
            f"https://adexchangebuyer.clients6.google.com"
            f"//v1internal/accounts/{self.account_id}/googleCuratedPackages"
        )
        params = {
            "query.filter": "",
            "query.pageSize": str(page_size),
            "query.pageNumber": "0",
            "query.orderBy": "last_update_time DESC",
            "key": self.api_key
        }
        
        all_packages = []
        page_number = 0
        
        logger.info("Starting Google Curated packages fetch...")
        
        while True:
            params["query.pageNumber"] = str(page_number)
            logger.info(f"Fetching Google Curated page {page_number + 1}...")
            
            headers = self.auth_manager.get_authenticated_headers()
            
            try:
                response = requests.get(url, params=params, headers=headers, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                packages = data.get("googleCuratedPackages", [])
                total_size = int(data.get("totalSize", 0))
                
                if not packages:
                    break
                
                all_packages.extend(packages)
                logger.info(f"Page {page_number + 1}: Found {len(packages)} packages (Total: {len(all_packages)}/{total_size})")
                
                # Check if we've fetched all packages
                if len(all_packages) >= total_size:
                    break
                
                page_number += 1
                time.sleep(0.5)  # Rate limiting
                
            except requests.exceptions.HTTPError as e:
                if response.status_code == 401:
                    logger.error("SAPISIDHASH authentication failed. Update tokens in .env file.")
                    raise ValueError("Authentication failed. Please refresh tokens.")
                else:
                    logger.error(f"HTTP {response.status_code} error: {response.text[:500]}")
                    raise
            except Exception as e:
                logger.error(f"Request failed: {e}")
                raise
        
        logger.info(f"Successfully fetched {len(all_packages)} Google Curated packages")
        return all_packages
