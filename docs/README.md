# Documentation

This directory contains technical documentation for the deal extraction and packaging project.

## Available Documents

### [unified-schema-field-definitions.md](./unified-schema-field-definitions.md) ⭐ **NEW**
**Complete Field Reference: Unified Schema & Enrichment Fields**

Comprehensive documentation for the unified deal schema used throughout the pipeline:
- **Pre-enrichment fields** (UnifiedPreEnrichmentSchema): 19 fields normalized across all vendors
- **Enrichment fields** (EnrichedDeal): Taxonomy, Safety, Audience, Commercial, and metadata fields
- **Phase 2 enhancements**: Taxonomy Validator, Publisher Intelligence, Temporal Signals
- Multi-vendor support (Google Authorized Buyers, Google Curated, BidSwitch)
- TSV export structure and usage examples

**Reference this** for understanding the unified schema, enrichment fields, and working with enriched deal data.

---

### [authentication-architecture.md](./authentication-architecture.md)
**Technical Note: Authorized Buyers API Authentication & Project Configuration**

Comprehensive documentation covering:
- SAPISIDHASH authentication method
- Manual token extraction from Chrome DevTools
- Authentication flow and architecture
- Troubleshooting checklist

**Read this first** if you encounter authentication issues or need to understand how authentication works with Authorized Buyers.

---

### [field-definitions.md](./field-definitions.md) 📜 **Legacy**
**Legacy Field Reference: Google Ads Marketplace TSV Schema**

Historical documentation for the original Google Ads Marketplace TSV export structure (246 columns). This document is preserved for reference but is **superseded by** `unified-schema-field-definitions.md` for current pipeline usage.

**Note**: The unified schema consolidates vendor-specific fields into a normalized structure. See `unified-schema-field-definitions.md` for the current schema.

---

## Quick Reference

### Schema & Data
- **Unified Schema**: See `unified-schema-field-definitions.md` for complete field reference
- **Pre-Enrichment Fields**: 19 fields normalized across vendors
- **Enrichment Fields**: Taxonomy, Safety, Audience, Commercial metadata
- **Schema Version**: 1.0

### Authentication
- **Authentication Method:** SAPISIDHASH (Manual browser tokens)
- **Project ID:** `bedrock-us-east`
- **Project Number:** `481844597274`
- **Required API:** Ad Exchange Buyer API II (legacy name for Authorized Buyers)
- **OAuth Scope:** `https://www.googleapis.com/auth/adexchange.buyer`
- **Internal API Endpoint:** `adexchangebuyer.clients6.google.com//v1internal/`

---

## Contributing

When adding new documentation:
1. Use clear, descriptive filenames
2. Include a summary at the top
3. Add cross-references to related docs
4. Update this README with new documents
