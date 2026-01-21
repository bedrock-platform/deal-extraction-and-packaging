# Ticket DEAL-401: Device Type Schema Enhancement & Microsoft Curated Ingestion

**Ticket ID:** DEAL-401  
**Title:** Add Device Type Field to Unified Schema & Ingest Microsoft Curated Inventory  
**Status:** TODO  
**Priority:** HIGH  
**Phase:** Phase 3 (Stage 2 & 3 Integration)  
**Created:** January 2026  
**Assigned To:** Development Team

---

## Description

This ticket addresses the critical gap identified in the Format and Device Identification Audit: our system lacks explicit device-level categorization, preventing proper distinction between CTV-only deals and multi-device deals. This aligns with industry standards (Microsoft Monetize, Beeswax DSP) where "Format" (what creative can run) and "Device" (which devices are targeted) are separate concerns.

**Key Problem**: A "Video" deal could be a small 300x250 outstream player on a blog (OLV) or a 60-second non-skippable ad on a 75-inch screen (CTV). Advertisers treat these as separate device-level budgets, but our current system groups them together.

**Solution**: 
1. Add `device_type` field to Unified Schema
2. Ingest Microsoft Curated CSVs as a new vendor source (provides explicit device signals)
3. Create Device Auditor for inference on existing deals
4. Update clustering to use device_type as high-weight feature
5. Update naming templates to include device in package names

---

## Business Value

- **Industry Alignment**: Matches Microsoft Monetize and Beeswax DSP standards (Format vs Device distinction)
- **Commercial Quality**: Prevents "junk" display/mobile video from diluting premium CTV packages
- **Buyer Budget Alignment**: CTV and Desktop/Mobile video are separate budget lines for advertisers
- **Package Quality**: Raises commercial quality of generated packages by ensuring device-appropriate clustering
- **North Star Compliance**: Package names explicitly call out device (e.g., "Verified News **CTV** Deal")
- **Filterability**: Enables device-based filtering at both deal and package levels

---

## Acceptance Criteria

### Schema & Data Model
- [ ] `device_type` field added to `UnifiedPreEnrichmentSchema` (Enum: `CTV`, `Mobile`, `Desktop`, `Tablet`, `All`)
- [ ] `device_type` field added to `EnrichedDeal` schema
- [ ] Device aggregation function added to `src/package_enrichment/aggregation.py`
- [ ] Format aggregation function enhanced to distinguish CTV/OTT

### Microsoft Curated Ingestion
- [ ] `MicrosoftCuratedTransformer` class created (extends `BaseTransformer`)
- [ ] CSV ingestion pipeline implemented for Microsoft Curated files
- [ ] Device field mapping: Microsoft `Device` → Unified `device_type`
- [ ] Format field mapping: Microsoft `SSP/Exchange` → Unified `format` + `format_subtype`
- [ ] Venue Type support for DOOH inventory (CTV-DOOH file)
- [ ] Integration with orchestrator (`src/common/orchestrator.py`)

### Device Inference & Auditor
- [ ] `DeviceAuditor` class created in `src/enrichment/device_auditor.py`
- [ ] Inference rules implemented:
  - `inventory_type: "ctv"` → `device_type: "CTV"`
  - `inventory_type: "apps"` → `device_type: "Mobile"`
  - `inventory_type: "websites"` → `device_type: "Desktop"`
  - Publisher name keywords (Pluto TV, Tubi, Sling → CTV)
  - BidSwitch `inventory_type: 3` → CTV (heuristic)
- [ ] Device inference integrated into Stage 1 enrichment pipeline
- [ ] Fallback logic: infer from deal name if other signals unavailable

### Clustering & Package Creation
- [ ] GMM clustering updated to use `device_type` as high-weight feature
- [ ] Clustering ensures CTV deals and Desktop/Mobile video deals cluster separately
- [ ] Package creation prompt updated to consider device_type in clustering decisions
- [ ] Device aggregation added to package enrichment output

### Naming & Templates
- [ ] `naming_templates.json` updated to require `[Device]` or `[Format]` prefix
- [ ] Naming convention updated: `[Quality] [Vertical/Audience] [Device] Package`
- [ ] Examples:
  - Old: "Premium Sports Enthusiast Video Package"
  - New: "Premium Sports Enthusiast **CTV** Package"
- [ ] Package grouping prompt updated to use device_type in naming

### Documentation
- [ ] Schema documentation updated (`docs/unified-schema-field-definitions.md`)
- [ ] Format and Device audit document updated with implementation status
- [ ] Microsoft Curated ingestion guide created

---

## Implementation Details

### Technical Approach

#### Phase 1: Schema Enhancement

**1.1 Add DeviceTypeEnum to Schema**

```python
# src/common/schema.py

class DeviceTypeEnum(str, Enum):
    """Valid device targeting values."""
    CTV = "ctv"
    MOBILE = "mobile"
    DESKTOP = "desktop"
    TABLET = "tablet"
    ALL = "all"  # Multi-device targeting
    DESKTOP_MOBILE = "desktop_mobile"
    DESKTOP_MOBILE_TABLET = "desktop_mobile_tablet"
    DESKTOP_MOBILE_TABLET_CTV = "desktop_mobile_tablet_ctv"
```

**1.2 Update UnifiedPreEnrichmentSchema**

```python
class UnifiedPreEnrichmentSchema(BaseModel):
    # ... existing fields ...
    device_type: Optional[DeviceTypeEnum] = Field(
        None,
        description="Device targeting: CTV, Mobile, Desktop, Tablet, All, or multi-device combinations"
    )
```

**1.3 Update EnrichedDeal Schema**

```python
class EnrichedDeal(BaseModel):
    # ... existing fields ...
    device_type: Optional[DeviceTypeEnum] = None
```

#### Phase 2: Microsoft Curated Ingestion

**2.1 Create MicrosoftCuratedTransformer**

```python
# src/microsoft_curated/transformer.py

class MicrosoftCuratedTransformer(BaseTransformer):
    """
    Transformer for Microsoft Curated CSV files.
    
    Handles:
    - Monetize Video (CTV and Online Video)
    - Monetize Display
    - Monetize Native
    - Monetize Audio
    - CTV-DOOH (with Venue Type)
    """
    
    def transform(self, row: Dict[str, Any]) -> UnifiedPreEnrichmentSchema:
        """
        Transform Microsoft CSV row to unified schema.
        
        Mapping:
        - Channel/Publisher → publishers (List)
        - Device → device_type (direct mapping)
        - SSP/Exchange → ssp_name + format inference
        - Content Category → description/concepts
        - Curated Deal ID → deal_id
        """
        # Device mapping
        device_mapping = {
            "CTV": DeviceTypeEnum.CTV,
            "Desktop & Mobile": DeviceTypeEnum.DESKTOP_MOBILE,
            "Mobile App": DeviceTypeEnum.MOBILE,
            "Desktop": DeviceTypeEnum.DESKTOP,
        }
        
        # Format inference from SSP/Exchange
        ssp_name = row.get("SSP/Exchange", "")
        format_val = self._infer_format_from_ssp(ssp_name)
        
        return UnifiedPreEnrichmentSchema(
            deal_id=row.get("Curated Deal ID", ""),
            deal_name=row.get("Channel/Publisher", ""),
            source="Microsoft Curated",
            ssp_name=ssp_name,
            format=format_val,
            device_type=device_mapping.get(row.get("Device"), None),
            publishers=[row.get("Channel/Publisher", "")],
            floor_price=self._extract_floor_price(row),
            inventory_type=self._infer_inventory_type(row),
            description=row.get("Content Category", ""),
            raw_deal_data=row
        )
    
    def _infer_format_from_ssp(self, ssp_name: str) -> FormatEnum:
        """Infer format from SSP/Exchange name."""
        ssp_lower = ssp_name.lower()
        if "video" in ssp_lower:
            return FormatEnum.VIDEO
        elif "display" in ssp_lower:
            return FormatEnum.DISPLAY
        elif "native" in ssp_lower:
            return FormatEnum.NATIVE
        elif "audio" in ssp_lower:
            return FormatEnum.AUDIO
        return FormatEnum.DISPLAY  # Default
    
    def _infer_inventory_type(self, row: Dict[str, Any]) -> Optional[str]:
        """Infer inventory_type from Device field."""
        device = row.get("Device", "").lower()
        if "ctv" in device:
            return "ctv"
        elif "mobile" in device:
            return "apps"
        elif "desktop" in device:
            return "websites"
        return None
```

**2.2 Create Microsoft Curated Client**

```python
# src/microsoft_curated/client.py

class MicrosoftCuratedClient(BaseClient):
    """
    Client for Microsoft Curated CSV files.
    
    Supports:
    - Monetize Video CSV
    - Monetize Display CSV
    - Monetize Native CSV
    - Monetize Audio CSV
    - CTV-DOOH CSV (with Venue Type)
    """
    
    def extract_deals(self, csv_path: str) -> List[Dict[str, Any]]:
        """Extract deals from Microsoft Curated CSV file."""
        import pandas as pd
        
        df = pd.read_csv(csv_path)
        return df.to_dict('records')
```

**2.3 Register in Orchestrator**

```python
# src/common/orchestrator.py

# Add Microsoft Curated to vendor list
SUPPORTED_VENDORS = {
    "google_ads": (GoogleAdsClient, GoogleAdsTransformer),
    "bidswitch": (BidSwitchClient, BidSwitchTransformer),
    "microsoft_curated": (MicrosoftCuratedClient, MicrosoftCuratedTransformer),  # New
}
```

#### Phase 3: Device Auditor

**3.1 Create DeviceAuditor**

```python
# src/enrichment/device_auditor.py

class DeviceAuditor:
    """
    Infers device_type for deals that don't have explicit device information.
    
    Uses multiple signals:
    1. inventory_type field (direct mapping)
    2. Publisher name keywords (CTV publishers)
    3. Deal name keywords
    4. Format + inventory_type combination
    """
    
    CTV_PUBLISHER_KEYWORDS = [
        "pluto", "tubi", "sling", "roku", "fire tv", "apple tv",
        "chromecast", "smart tv", "disney+", "paramount+", "hulu",
        "peacock", "netflix", "hbo max", "discovery+"
    ]
    
    CTV_DEAL_NAME_KEYWORDS = ["ctv", "connected tv", "ott", "streaming"]
    
    def infer_device_type(
        self,
        deal: UnifiedPreEnrichmentSchema
    ) -> Optional[DeviceTypeEnum]:
        """
        Infer device_type from deal metadata.
        
        Priority:
        1. Explicit device_type (if already set)
        2. inventory_type mapping
        3. Publisher name keywords
        4. Deal name keywords
        5. Format + inventory_type combination
        """
        # Already has device_type
        if deal.device_type:
            return deal.device_type
        
        # Check inventory_type
        if deal.inventory_type:
            inv_type_str = str(deal.inventory_type).lower()
            if inv_type_str == "ctv" or inv_type_str == "3":  # BidSwitch code
                return DeviceTypeEnum.CTV
            elif inv_type_str == "apps":
                return DeviceTypeEnum.MOBILE
            elif inv_type_str == "websites":
                return DeviceTypeEnum.DESKTOP
        
        # Check publisher names
        publishers_str = " ".join(deal.publishers).lower()
        if any(keyword in publishers_str for keyword in self.CTV_PUBLISHER_KEYWORDS):
            return DeviceTypeEnum.CTV
        
        # Check deal name
        deal_name_lower = deal.deal_name.lower()
        if any(keyword in deal_name_lower for keyword in self.CTV_DEAL_NAME_KEYWORDS):
            return DeviceTypeEnum.CTV
        
        # Format + inventory_type combination
        if deal.format == FormatEnum.VIDEO and deal.inventory_type:
            inv_type_str = str(deal.inventory_type).lower()
            if "ctv" in inv_type_str:
                return DeviceTypeEnum.CTV
        
        return None  # Cannot infer
```

**3.2 Integrate into Enrichment Pipeline**

```python
# src/enrichment/inference.py

def enrich_deal_unified(
    deal: UnifiedPreEnrichmentSchema,
    llm_client: GeminiClient,
    volume_context: Optional[str] = None
) -> EnrichedDeal:
    """Enrich deal with semantic metadata."""
    
    # ... existing enrichment ...
    
    # Device inference (if not already set)
    from .device_auditor import DeviceAuditor
    device_auditor = DeviceAuditor()
    device_type = device_auditor.infer_device_type(deal)
    
    # ... create EnrichedDeal with device_type ...
```

#### Phase 4: Clustering Updates

**4.1 Update Clustering to Use Device Type**

```python
# src/package_creation/clustering.py

def create_deal_embeddings_with_device(
    deals: List[Dict[str, Any]],
    embedding_model: str = "all-MiniLM-L6-v2"
) -> np.ndarray:
    """
    Create embeddings with device_type as high-weight feature.
    
    Strategy:
    - Include device_type in embedding text
    - Weight device_type higher than other features
    - Ensures CTV deals cluster separately from Desktop/Mobile video
    """
    from sentence_transformers import SentenceTransformer
    
    model = SentenceTransformer(embedding_model)
    
    # Create text representations with device emphasis
    texts = []
    for deal in deals:
        # Build text with device_type as prominent feature
        device = deal.get("device_type", "unknown")
        format_val = deal.get("format", "unknown")
        taxonomy = deal.get("taxonomy", {})
        
        # Device gets high weight in text representation
        text = f"DEVICE:{device} FORMAT:{format_val} "
        if taxonomy.get("tier1"):
            text += f"TAXONOMY:{taxonomy['tier1']} "
        if deal.get("deal_name"):
            text += f"NAME:{deal['deal_name']}"
        
        texts.append(text)
    
    return model.encode(texts)
```

**4.2 Update Package Creation Prompt**

```python
# config/package_creation/package_grouping_prompt.txt

# Add section about device_type:

## Device Targeting Considerations

**CRITICAL**: Device type is a primary differentiator for buyer budgets:
- **CTV deals** should be clustered separately from Desktop/Mobile video deals
- A "Video" deal on CTV (75-inch screen) is fundamentally different from a "Video" deal on Desktop (300x250 player)
- Do NOT cluster CTV deals with Desktop/Mobile video deals, even if they share taxonomy

**Device Types**:
- `CTV`: Connected TV devices (Roku, Fire TV, Apple TV, Smart TVs)
- `Mobile`: Mobile apps
- `Desktop`: Desktop websites
- `All` or multi-device: Targets multiple device types

**Clustering Rules**:
- CTV deals → CTV-only packages
- Desktop/Mobile video deals → Desktop/Mobile packages
- Multi-device deals → Can appear in multiple packages (one per device type)
```

#### Phase 5: Format & Device Aggregation

**5.1 Add Format Aggregation Function**

```python
# src/package_enrichment/aggregation.py

def aggregate_format(deals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate format data from deals.
    
    Distinguishes CTV/OTT from generic video.
    """
    from collections import Counter
    
    formats = []
    inventory_types = []
    device_types = []
    
    for deal in deals:
        format_val = deal.get("format")
        if format_val:
            formats.append(format_val)
        
        inventory_type = deal.get("inventory_type")
        if inventory_type:
            inventory_types.append(str(inventory_type).lower())
        
        device_type = deal.get("device_type")
        if device_type:
            device_types.append(str(device_type).lower())
    
    # Determine if CTV/OTT
    has_ctv = (
        any('ctv' in inv_type for inv_type in inventory_types) or
        any('ctv' in dev_type for dev_type in device_types)
    )
    
    # Create format list with CTV distinction
    format_list = list(set(formats))
    if has_ctv and 'video' in format_list:
        format_list.append('ctv_ott')
    
    return {
        'formats': format_list,
        'dominant_format': Counter(formats).most_common(1)[0][0] if formats else None,
        'format_distribution': dict(Counter(formats)),
        'has_ctv': has_ctv,
        'inventory_types': list(set(inventory_types))
    }
```

**5.2 Add Device Aggregation Function**

```python
# src/package_enrichment/aggregation.py

def aggregate_device(deals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Aggregate device targeting from deals.
    
    Returns device list and targeting type.
    """
    devices = set()
    
    for deal in deals:
        device_type = deal.get("device_type")
        if device_type:
            device_str = str(device_type).lower()
            # Handle enum values
            if device_str == "ctv":
                devices.add("ctv")
            elif device_str == "mobile":
                devices.add("mobile")
            elif device_str == "desktop":
                devices.add("desktop")
            elif device_str == "tablet":
                devices.add("tablet")
            elif device_str == "all" or "_" in device_str:
                # Multi-device: parse
                if "ctv" in device_str:
                    devices.add("ctv")
                if "mobile" in device_str:
                    devices.add("mobile")
                if "desktop" in device_str:
                    devices.add("desktop")
                if "tablet" in device_str:
                    devices.add("tablet")
        
        # Fallback: infer from inventory_type
        if not devices:
            inventory_type = deal.get("inventory_type")
            if inventory_type:
                inv_type_str = str(inventory_type).lower()
                if 'ctv' in inv_type_str or inv_type_str == "3":
                    devices.add('ctv')
                if 'websites' in inv_type_str:
                    devices.add('desktop')
                if 'apps' in inv_type_str:
                    devices.add('mobile')
    
    device_list = sorted(list(devices))
    
    # Determine targeting type
    if device_list == ['ctv']:
        targeting_type = 'ctv_only'
    elif 'ctv' in device_list and len(device_list) > 1:
        targeting_type = 'multi_device_including_ctv'
    elif len(device_list) > 1:
        targeting_type = 'multi_device'
    elif len(device_list) == 1:
        targeting_type = 'single_device'
    else:
        targeting_type = 'unknown'
    
    return {
        'devices': device_list,
        'device_targeting_type': targeting_type,
        'has_ctv': 'ctv' in device_list
    }
```

**5.3 Integrate into Package Enrichment**

```python
# src/package_enrichment/enricher.py

def enrich_package(self, package: Dict[str, Any], deals: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Enrich package with aggregated metadata."""
    
    # ... existing aggregation ...
    
    # Add format and device aggregation
    format_data = aggregate_format(deals)
    device_data = aggregate_device(deals)
    
    # Add to package output
    enriched_package = {
        # ... existing fields ...
        'format': format_data,
        'device': device_data,
    }
    
    return enriched_package
```

#### Phase 6: Naming Template Updates

**6.1 Update Naming Templates**

```json
// config/package_creation/naming_templates.json

{
  "naming_convention": "[Quality] [Vertical/Audience] [Device] Package",
  "device_naming_rules": {
    "ctv_only": "[Quality] [Vertical/Audience] CTV Package",
    "multi_device_including_ctv": "[Quality] [Vertical/Audience] [Format] (Multi-Device) Package",
    "desktop_mobile": "[Quality] [Vertical/Audience] Desktop & Mobile Package",
    "mobile_only": "[Quality] [Vertical/Audience] Mobile Package"
  },
  "examples": {
    "ctv": "Premium Auto Intender CTV Package",
    "multi_device": "Premium Sports Enthusiast Video (Desktop, Mobile, Tablet, CTV) Package",
    "desktop_mobile": "Essential News & Information Desktop & Mobile Package"
  }
}
```

**6.2 Update Package Grouping Prompt**

```python
# config/package_creation/package_grouping_prompt.txt

# Add device naming guidance:

## Package Naming with Device

Package names MUST include device type when relevant:
- CTV-only packages: "[Quality] [Vertical/Audience] CTV Package"
- Multi-device packages: "[Quality] [Vertical/Audience] [Format] (Desktop, Mobile, Tablet, CTV) Package"
- Desktop/Mobile packages: "[Quality] [Vertical/Audience] Desktop & Mobile Package"

**Examples**:
- ✅ "Premium Auto Intender CTV Package" (CTV-only)
- ✅ "Essential News & Information Desktop & Mobile Package" (Desktop/Mobile)
- ✅ "Performance Sports Video (Desktop, Mobile, Tablet, CTV) Package" (Multi-device)
- ❌ "Premium Sports Video Package" (Missing device - too generic)
```

### Code Changes

**New Files**:
- `src/microsoft_curated/__init__.py`
- `src/microsoft_curated/client.py` - CSV ingestion client
- `src/microsoft_curated/transformer.py` - Microsoft → Unified schema transformer
- `src/enrichment/device_auditor.py` - Device inference logic

**Modified Files**:
- `src/common/schema.py` - Add `DeviceTypeEnum` and `device_type` field
- `src/enrichment/inference.py` - Integrate DeviceAuditor
- `src/package_creation/clustering.py` - Update embeddings to include device_type
- `src/package_enrichment/aggregation.py` - Add `aggregate_format()` and `aggregate_device()`
- `src/package_enrichment/enricher.py` - Include format/device in package output
- `src/common/orchestrator.py` - Register Microsoft Curated vendor
- `config/package_creation/naming_templates.json` - Add device naming rules
- `config/package_creation/package_grouping_prompt.txt` - Add device clustering/naming guidance
- `docs/unified-schema-field-definitions.md` - Document device_type field

### Dependencies

- [ ] Microsoft Curated CSV files available (Monetize Video, Display, Native, Audio, CTV-DOOH)
- [ ] Schema migration plan for existing deals (backfill device_type)
- [ ] Testing with Microsoft Curated sample data

---

## Testing

### Unit Tests

- [ ] `DeviceAuditor.infer_device_type()` tests:
  - CTV inference from inventory_type
  - CTV inference from publisher keywords
  - CTV inference from deal name
  - Desktop/Mobile inference
  - Fallback behavior

- [ ] `MicrosoftCuratedTransformer.transform()` tests:
  - Device field mapping
  - Format inference from SSP/Exchange
  - Venue Type handling (DOOH)
  - Edge cases (missing fields)

- [ ] `aggregate_format()` tests:
  - CTV/OTT distinction
  - Format distribution
  - Mixed format packages

- [ ] `aggregate_device()` tests:
  - CTV-only packages
  - Multi-device packages
  - Device targeting type classification

### Integration Tests

- [ ] Microsoft Curated CSV ingestion end-to-end
- [ ] Device inference in enrichment pipeline
- [ ] Clustering with device_type (CTV vs Desktop/Mobile separation)
- [ ] Package naming with device_type
- [ ] Format/device aggregation in package enrichment

### Manual Testing

- [ ] Ingest Microsoft Curated CSV files
- [ ] Verify device_type populated correctly
- [ ] Verify CTV deals cluster separately from Desktop/Mobile video
- [ ] Verify package names include device (e.g., "Premium Auto Intender CTV Package")
- [ ] Verify format/device fields in package enrichment output

---

## Related Tickets

- **Related to**: DEAL-305 (North Star Naming Taxonomy) - Device naming extends naming taxonomy
- **Blocks**: Future device-based filtering features
- **References**: Format and Device Identification Audit (`docs/format_and_device_identification_audit.md`)

---

## Notes

### Microsoft Curated CSV Structure

**Monetize Video CSV**:
- Channel/Publisher
- Device (CTV, Desktop & Mobile, Mobile App, Desktop)
- SSP/Exchange (Monetize Video)
- Content Category
- Curated Deal ID

**CTV-DOOH CSV**:
- Additional: Venue Type (Bars & Clubs, Malls, etc.)
- Device: CTV
- Format: Video

### Migration Strategy for Existing Deals

**Backfill Approach**:
1. Run DeviceAuditor on all existing deals
2. Update `device_type` field in enriched deals
3. Re-run package creation with device-aware clustering
4. Update package names to include device

**Priority**: High-value deals first (Premium tier, high volume)

### Performance Considerations

- Device inference is lightweight (string matching, no LLM calls)
- Clustering with device_type may create more clusters (expected - better separation)
- Format/device aggregation adds minimal overhead to package enrichment

---

**Last Updated:** January 2026
