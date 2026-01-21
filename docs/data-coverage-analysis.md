# Data Coverage Analysis

## Comparison: UI Side Panel vs. TSV Export

### ✅ Captured Fields

| UI Field | TSV Column Name | Status |
|----------|----------------|--------|
| Package name | `Name` | ✅ Captured |
| Deal ID | `ID` | ✅ Captured |
| Description | `Description` | ✅ Captured |
| Content type | `Content Type` | ✅ Captured |
| Package type | `Package Type` | ✅ Captured |
| Weekly forecast - Impressions | `Impressions` | ✅ Captured |
| Weekly forecast - Uniques | `Uniques` | ✅ Captured |
| CPM breakdown | `Avg CPM (USD)`, `Min CPM (USD)`, `Max CPM (USD)`, `Median CPM (USD)` | ✅ Captured |
| Gender breakdown | `GENDER_Male_Impressions`, `GENDER_Female_Impressions`, etc. | ✅ Captured (all slices) |
| User geo | `COUNTRY_United States_Impressions`, etc. | ✅ Captured (all slices) |
| Age breakdown | `AGE_45-54_Impressions`, `AGE_55-64_Impressions`, etc. | ✅ Captured (all slices) |
| Device breakdown | `DEVICE_Desktop_Impressions`, `DEVICE_Mobile_Impressions`, etc. | ✅ Captured (all slices) |
| Vertical | `CONTENT_VERTICAL_Arts & Entertainment_Impressions`, etc. | ✅ Captured (all slices) |
| Format (Display/Video) | `REQUEST_FORMAT_Display and Video_Impressions`, etc. | ✅ Captured (all slices) |
| Video duration | `VIDEO_DURATION_Up to 15s_Impressions`, etc. | ✅ Captured (all slices) |
| Publisher | `Publisher` | ✅ Captured |
| Publisher Account ID | `Publisher Account ID` | ✅ Captured |

### ❌ Missing Fields (Not Available in API Response)

These fields are shown in the UI side panel but are **NOT available** in the `inventoryViews:search` API response:

| UI Field | Reason |
|----------|--------|
| **Created by** | Not in API response |
| **Package floor price** | Not in API response |
| **Email contact** | Not in API response |
| **Inventory size** (ad sizes like 300x250, 320x50) | Not in API response - may require separate endpoint |
| **Top sites and apps** (yahoo.com, mail.yahoo.com) | Not in API response - may require separate endpoint |

### Breakdown Types Captured

We capture **all 7 breakdown types** available in the API:
1. ✅ `AGE` - Age ranges (18-24, 25-34, 35-44, etc.)
2. ✅ `GENDER` - Gender (Male, Female, Unknown)
3. ✅ `COUNTRY` - Geographic locations
4. ✅ `DEVICE` - Device types (Desktop, Mobile, Tablet)
5. ✅ `REQUEST_FORMAT` - Format types (Display and Video, Display only, Video only, etc.)
6. ✅ `CONTENT_VERTICAL` - Content categories (Arts & Entertainment, News, etc.)
7. ✅ `VIDEO_DURATION` - Video duration ranges (Up to 15s, 16s-20s, etc.)

### Data Structure

- **Summary columns**: Top-level fields (Name, ID, Description, etc.) + Primary breakdown slices
- **Flattened slice columns**: All unique slice values across all entities as separate columns
  - Format: `{FILTER_TYPE}_{SliceName}_Impressions`
  - Example: `AGE_45-54_Impressions`, `COUNTRY_United States_Impressions`

### Notes

1. **Missing fields** (Created by, Floor price, Email, Inventory size, Top sites/apps) are likely:
   - Available in a different API endpoint (e.g., deal details endpoint)
   - Only shown in the UI after drilling into a specific deal
   - Calculated/derived on the frontend

2. **All available breakdown data is captured** - we're capturing 100% of the breakdown slices provided by the API.

3. **Total columns**: Currently 246 columns (43 summary columns + ~203 flattened slice columns)

### Recommendations

If you need the missing fields:
1. **Inventory size (ad sizes)**: May require querying a separate endpoint or deal details API
2. **Top sites and apps**: Likely requires a separate API call to get domain/app breakdown
3. **Created by, Floor price, Email**: May be available in deal metadata endpoint (not inventory views)

Would you like me to investigate if these fields are available in other API endpoints?
