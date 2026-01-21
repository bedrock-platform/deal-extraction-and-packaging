"""
BidSwitch Package

A standalone package for integrating BidSwitch Deals Discovery API into Python projects.

Provides:
- BidSwitchClient: OAuth2-authenticated client for fetching deals
- BidSwitchTransformer: Transformer for converting BidSwitch deals to your schema
"""

from .client import BidSwitchClient
from .transformer import BidSwitchTransformer

__version__ = "1.0.0"
__all__ = ["BidSwitchClient", "BidSwitchTransformer"]
