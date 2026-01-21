# Device Type Enhancement Plan

## Overview

This plan addresses the critical gap in device-level categorization identified in the Format and Device Identification Audit. The system currently lacks explicit device-level fields, preventing proper distinction between CTV-only deals and multi-device deals.

## Problem Statement

Advertisers treat CTV and Desktop/Mobile video as separate device-level budgets, but our current system groups them together because:
- No explicit `device_type` field exists in the unified schema
- CTV/OTT format is not distinguished from generic "video" format
- Format/device information is not explicitly aggregated at package level

This misalignment prevents proper clustering and package naming that matches industry standards (Microsoft Monetize, Beeswax DSP).

## Solution

1. **Add `device_type` field** to Unified Schema (Enum: CTV, Mobile, Desktop, Tablet, All)
2. **Ingest Microsoft Curated CSVs** as a new vendor source (provides explicit device signals)
3. **Create Device Auditor** for inference on existing deals
4. **Update clustering** to use device_type as high-weight feature
5. **Update naming templates** to include device in package names

## Tickets

- **DEAL-401**: Device Type Schema Enhancement & Microsoft Curated Ingestion

## Related Documentation

- **Audit Document**: `docs/format_and_device_identification_audit.md`
- **Schema Definitions**: `docs/unified-schema-field-definitions.md`
- **Naming Templates**: `config/package_creation/naming_templates.json`

## Status

**Status**: Planning  
**Priority**: HIGH  
**Created**: January 2026

---

**Last Updated**: January 2026
