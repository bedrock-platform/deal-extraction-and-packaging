"""
BidSwitch API Client

Implements BaseSSPClient for BidSwitch Deals Discovery API.
Handles OAuth2 authentication and deal discovery.

This is a standalone client that can be integrated into any Python project.
"""
import os
import time
import requests
from typing import Dict, List, Any, Optional

from ..common.base_client import BaseSSPClient


class BidSwitchClient(BaseSSPClient):
    """
    BidSwitch API client implementing BaseSSPClient interface.
    
    Requires environment variables:
    - BIDSWITCH_USERNAME: Your BidSwitch username
    - BIDSWITCH_PASSWORD: Your BidSwitch password
    - DSP_SEAT_ID: Your DSP seat ID (required for API calls)
    """
    
    def __init__(self, username: Optional[str] = None, password: Optional[str] = None, dsp_seat_id: Optional[str] = None):
        """
        Initialize BidSwitch client.
        
        Args:
            username: BidSwitch username (if None, reads from BIDSWITCH_USERNAME env var)
            password: BidSwitch password (if None, reads from BIDSWITCH_PASSWORD env var)
            dsp_seat_id: DSP seat ID (if None, reads from DSP_SEAT_ID env var)
        """
        self.username = username or os.getenv('BIDSWITCH_USERNAME')
        self.password = password or os.getenv('BIDSWITCH_PASSWORD')
        self.dsp_seat_id = dsp_seat_id or os.getenv('DSP_SEAT_ID')
        self.bidswitch_token = None
        self.token_expiry = None
        
        if not self.username or not self.password:
            raise ValueError(
                "BIDSWITCH_USERNAME and BIDSWITCH_PASSWORD must be provided "
                "either as arguments or environment variables"
            )
        
        if not self.dsp_seat_id:
            raise ValueError(
                "DSP_SEAT_ID must be provided either as argument or environment variable"
            )
        
        self.authenticate()
    
    def authenticate(self) -> bool:
        """Authenticate to BidSwitch API using OAuth2 with username/password."""
        try:
            # Strip whitespace that may come from Kubernetes secrets or config files
            username = self.username.strip()
            password = self.password.strip()
            
            if not username or not password:
                raise ValueError("BidSwitch credentials are empty after sanitization")
            
            # OAuth2 authentication endpoint
            auth_url = "https://iam.bidswitch.com/auth/realms/bidswitch/protocol/openid-connect/token"
            
            auth_data = {
                'client_id': 'public-client',
                'grant_type': 'password',
                'username': username,
                'password': password,
                'scope': 'openid email profile'
            }
            
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded'
            }
            
            response = requests.post(auth_url, headers=headers, data=auth_data, timeout=30)
            
            if response.status_code != 200:
                raise ValueError(
                    f"BidSwitch OAuth2 authentication failed: {response.status_code} - {response.text[:200]}"
                )
            
            token_data = response.json()
            self.bidswitch_token = token_data.get('access_token')
            
            if not self.bidswitch_token:
                raise ValueError("BidSwitch OAuth2 authentication failed: No access token in response")
            
            # Calculate token expiry (default to 10 minutes if expires_in missing)
            expires_in = token_data.get('expires_in', 600)
            self.token_expiry = time.time() + expires_in
            
            return True
            
        except Exception as e:
            raise ValueError(f"BidSwitch authentication error: {e}")
    
    def is_authenticated(self) -> bool:
        """Check if client is authenticated"""
        return self.bidswitch_token is not None
    
    def _ensure_token_valid(self):
        """Refresh token if it's expired or about to expire."""
        if not self.bidswitch_token or (self.token_expiry and time.time() >= self.token_expiry - 60):
            self.authenticate()
    
    def get_vendor_name(self) -> str:
        """Get vendor name"""
        return "BidSwitch"
    
    def discover_deals(
        self,
        inventory_format: Optional[str] = None,
        countries: Optional[str] = None,
        floor_price_max: Optional[float] = None,
        floor_price_min: Optional[float] = None,
        auction_type: Optional[str] = None,
        inventory_types: Optional[str] = None,
        device_types: Optional[str] = None,
        publishers: Optional[str] = None,
        urg_owners: Optional[str] = None,
        inventory_highlights: Optional[str] = None,
        deal_id: Optional[str] = None,
        display_name: Optional[str] = None,
        ssp_id: Optional[int] = None,
        is_activated: Optional[bool] = None,
        limit: Optional[int] = 100,
        offset: Optional[int] = None,
        max_pages: Optional[int] = None,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Discover available deals from BidSwitch Deals Discovery API.

        This endpoint returns draft/offer deals that SSPs have made available to the open market.
        These are deals that can be activated (not existing active deals).

        Args:
            inventory_format: Ad format filter ("video", "display")
            countries: ISO Alpha-2 country codes, comma-separated (e.g., "US", "CA", "GB")
            floor_price_max: Maximum CPM willing to pay (float)
            floor_price_min: Minimum CPM filter (float)
            auction_type: Auction mechanics ("first_price", "fixed")
            inventory_types: Environment types, comma-separated ("app", "web", "ctv")
            device_types: Device targeting, comma-separated ("PC", "Phone", "Tablet", "CTV", "MediaCenter")
            publishers: Publisher domain/name filter
            urg_owners: Under-Represented Group filter ("minority_owned")
            inventory_highlights: Content category filter, comma-separated
            deal_id: Specific deal ID to lookup
            display_name: Search by deal name (partial match supported)
            ssp_id: Filter by specific SSP ID (7=Sovrn, 68=Nexxen, 6=OpenX, 1=Magnite, 52=Sonobi, 255=Commerce Grid)
            is_activated: Filter activated vs not-activated deals
            limit: Maximum results to return (default: 100)
            offset: Pagination offset
            max_pages: Maximum pages to fetch (default: 3)
            **kwargs: Additional vendor-specific parameters

        Returns:
            List of deal objects in BidSwitch native format

        Raises:
            ValueError: If API request fails or authentication fails
        """
        try:
            self._ensure_token_valid()
            
            api_url = f"https://api.bidswitch.com/api/v1/dsp/{self.dsp_seat_id}/deals_discovery/"
            
            # Build query parameters (only include non-None values)
            params = {}
            if inventory_format:
                params['inventory_format'] = inventory_format
            if countries:
                params['countries'] = countries
            if floor_price_max is not None:
                params['floor_price_max'] = floor_price_max
            if floor_price_min is not None:
                params['floor_price_min'] = floor_price_min
            if auction_type:
                params['auction_type'] = auction_type
            if inventory_types:
                params['inventory_types'] = inventory_types
            if device_types:
                params['device_types'] = device_types
            if publishers:
                params['publishers'] = publishers
            if urg_owners:
                params['urg_owners'] = urg_owners
            if deal_id:
                params['deal_id'] = deal_id
            if display_name:
                params['display_name'] = display_name
            if ssp_id is not None:
                params['ssp_id'] = ssp_id
            if is_activated is not None:
                params['is_activated'] = is_activated
            if limit:
                params['limit'] = limit
            
            headers = {
                "Authorization": f"Bearer {self.bidswitch_token}",
                "Content-Type": "application/json"
            }
            
            # Pagination support
            all_deals = []
            current_offset = offset or 0
            page_count = 0
            max_pages_to_fetch = max_pages if max_pages else 3
            
            while True:
                page_params = params.copy()
                if current_offset > 0:
                    page_params['offset'] = current_offset
                
                page_response = requests.get(api_url, params=page_params, headers=headers, timeout=30)
                
                # If 401, token might have expired, try refreshing once
                if page_response.status_code == 401 and page_count == 0:
                    self.authenticate()
                    headers["Authorization"] = f"Bearer {self.bidswitch_token}"
                    page_response = requests.get(api_url, params=page_params, headers=headers, timeout=30)
                
                if page_response.status_code != 200:
                    break
                
                response_text = page_response.text.strip()
                if not response_text:
                    break
                
                try:
                    deals = page_response.json()
                except ValueError:
                    break
                
                page_count += 1
                
                # Parse response
                if isinstance(deals, list):
                    deals_list = deals
                    has_next = False
                elif isinstance(deals, dict):
                    if 'results' in deals:
                        deals_list = deals['results']
                        has_next = bool(deals.get('next'))
                    elif 'deals' in deals:
                        deals_list = deals['deals']
                        has_next = False
                    else:
                        deals_list = []
                        has_next = False
                else:
                    deals_list = []
                    has_next = False
                
                # Apply client-side filtering for inventory_highlights if specified
                if inventory_highlights and deals_list:
                    highlight_filters = [h.strip().lower() for h in inventory_highlights.split(',') if h.strip()]
                    if highlight_filters:
                        filtered_deals = []
                        for deal in deals_list:
                            deal_highlights = deal.get('inventory_highlights', [])
                            if isinstance(deal_highlights, list):
                                deal_highlight_lower = [str(h).lower() for h in deal_highlights]
                                if any(filter_h in ' '.join(deal_highlight_lower) or filter_h in deal_highlight_lower for filter_h in highlight_filters):
                                    filtered_deals.append(deal)
                            elif isinstance(deal_highlights, str):
                                deal_highlight_lower = deal_highlights.lower()
                                if any(filter_h in deal_highlight_lower for filter_h in highlight_filters):
                                    filtered_deals.append(deal)
                        deals_list = filtered_deals
                
                all_deals.extend(deals_list)
                
                # Check if we should continue paginating
                if not has_next or len(deals_list) == 0:
                    break
                
                if page_count >= max_pages_to_fetch:
                    break
                
                # Move to next page
                page_size = len(deals_list)
                current_offset += page_size
                time.sleep(0.5)  # Small delay between pages
            
            return all_deals
            
        except requests.exceptions.RequestException as e:
            raise ValueError(f"BidSwitch API request failed: {e}")
        except Exception as e:
            raise
