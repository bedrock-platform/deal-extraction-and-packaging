# Google Curated Packages Exploration

**Date:** 2026-01-20  
**Status:** Initial exploration complete

---

## Key Findings

### 1. Endpoint Structure

**List Endpoint:**
- **URL:** `GET /v1internal/accounts/{accountId}/googleCuratedPackages`
- **Response Structure:**
  ```json
  {
    "googleCuratedPackages": [...],
    "totalSize": 228
  }
  ```

**Detail Endpoint:**
- **URL:** `GET /v1internal/accounts/{accountId}/auctionPackages/{packageId}`
- **Note:** Uses `auctionPackages` (not `marketplacePackages`) but same pattern
- **Package ID:** `externalDealId` field

### 2. Data Structure Differences

| Field | Marketplace Packages | Google Curated Packages |
|-------|---------------------|------------------------|
| **Package ID** | `entityId` | `externalDealId` |
| **Forecast Data** | `forecast.breakdowns[]` (with slices) | `forecastMetrics` (impressions/uniques only) |
| **Breakdowns** | ✅ Full breakdowns (age, gender, country, etc.) | ❌ No breakdowns available |
| **Targeting** | ❌ Not in list response | ✅ `targeting[]` array with criteria |
| **Created By** | From hydration endpoint | ✅ `createdBy.displayName` in list |
| **Email Contact** | From hydration endpoint | ❓ Need to check detail endpoint |
| **Floor Price** | From hydration endpoint | ❓ Need to check detail endpoint |
| **CPM Histogram** | ✅ `costHistogramMetrics[]` | ❓ Not in list response |

### 3. Google Curated Package Structure

```json
{
  "auctionPackage": {
    "externalDealId": "549644393850040662",
    "createdBy": {
      "accountId": "239142378",
      "displayName": "Google Curated Packages"
    },
    "name": "GCP JP Investment Focused",
    "description": "GCP JP Investment Focused",
    "creationTime": "2025-01-20T12:09:28.597Z",
    "updateTime": "2025-12-22T17:57:58.643Z",
    "targeting": [
      {
        "targetingType": "TARGETING_TYPE_COUNTRY",
        "includedValues": [{"id": "2392", "displayName": "Japan"}]
      },
      {
        "targetingType": "TARGETING_TYPE_CONTENT_VERTICAL",
        "includedValues": [...]
      }
      // ... more targeting criteria
    ],
    "gcpInfo": {"isDiscoverable": true},
    "status": "ACTIVE",
    "creatorRole": "GOOGLE"
  },
  "forecastMetrics": {
    "impressions": "281000000",
    "uniqueUsers": "5833000"
  },
  "contentType": "CONTENT_TYPE_OTHER"
}
```

### 4. Critical Questions

1. **Can we get forecast breakdowns for Google Curated?**
   - ❓ Try `inventoryViews:search` with `entityCategories: ["GOOGLE_CURATED_PACKAGE"]` or `["AUCTION_PACKAGE"]`
   - ❓ Check if there's a different endpoint for forecast data

2. **Does `auctionPackages/{id}` provide email/floor price?**
   - ✅ Detail endpoint works (tested)
   - ❓ Need to check if it has `sellerContacts` and `priorityFloorPrice`

3. **Can we use the same export logic?**
   - ⚠️ **Different structure** - no forecast breakdowns in list response
   - ⚠️ **Different ID field** - `externalDealId` vs `entityId`
   - ✅ **Same hydration pattern** - `auctionPackages/{id}` works

---

## Next Steps

1. **Test `inventoryViews:search` for Google Curated:**
   - Try `entityCategories: ["GOOGLE_CURATED_PACKAGE"]`
   - Try `entityCategories: ["AUCTION_PACKAGE"]`
   - Check if forecast breakdowns are available

2. **Check detail endpoint for metadata:**
   - Verify if `auctionPackages/{id}` has `sellerContacts`
   - Verify if `auctionPackages/{id}` has `priorityFloorPrice`
   - Check for CPM histogram data

3. **Implement Google Curated export:**
   - Create separate fetch method for Google Curated
   - Adapt export logic for different structure (no breakdowns)
   - Export to "Google Curated" worksheet

---

## Sample Data

**Total Packages:** 228 Google Curated packages found

**Sample Package:**
- **ID:** `549644393850040662`
- **Name:** "GCP JP Investment Focused"
- **Impressions:** 281M
- **Uniques:** 5.8M
- **Targeting:** Japan, Investment Banking, Direct sellers, 70% viewability
