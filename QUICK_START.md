# Quick Start Guide

## SAPISIDHASH Authentication (Recommended)

This is the primary authentication method. Extract tokens from Chrome DevTools.

### Step-by-Step: Getting Your Credentials from Chrome DevTools

### 1. Open Chrome DevTools
- Press `F12` or right-click → **Inspect**
- Go to the **Network** tab

### 2. Trigger the API Request
- Navigate to the inventory views page in Authorized Buyers UI
- The `inventoryViews:search` request should appear in the Network tab

### 3. Copy Credentials

#### Find the Request
- Look for a request named `inventoryViews:search`
- Click on it to view details

#### Copy SAPISIDHASH
1. In the **Headers** tab, scroll to **Request Headers**
2. Find the `authorization` header
3. You'll see: `SAPISIDHASH 1768473013198_6ae15f8eef6e2ee384572a5d2c288471a68b7427`
4. Copy the entire value (including "SAPISIDHASH " prefix is fine)
5. Paste into `.env` as `AUTHORIZED_BUYERS_SAPISIDHASH=...`

#### Copy Cookies
1. Still in **Request Headers**, find the `cookie` header
2. Right-click on the cookie value → **Copy value**
3. The cookie string is very long (contains many cookies separated by `; `)
4. Paste into `.env` as `AUTHORIZED_BUYERS_COOKIES=...` (keep it all on one line)

### 4. Example .env File

```env
AUTHORIZED_BUYERS_ACCOUNT_ID=7287432622
AUTHORIZED_BUYERS_API_KEY=AIzaSyDntWfIQs0iyimIUm1GTOWjx5fJL8YdKTE
AUTHORIZED_BUYERS_SAPISIDHASH=1768473013198_6ae15f8eef6e2ee384572a5d2c288471a68b7427
AUTHORIZED_BUYERS_COOKIES=XSRF-TOKEN=AFCo3MCuMbW6uaZMCicHPbOpbz17ROkt9A:1761828754296; S=billing-ui-v3=f8rXrlcuAcw8aTK1JMUJY84Pd35HLSwzLPltrv4J49o; ... (rest of cookies)
```

**Note:** Tokens expire every ~60 minutes. When you get a 401 error, copy fresh values from Chrome DevTools.

### 5. Run the Script

```bash
python -m src.google_ads.inventory_downloader
```

---

## Alternative: Bearer Token

If you see `Authorization: Bearer ...` instead of SAPISIDHASH in Chrome DevTools:

1. Copy the Bearer token value
2. Paste into `.env` as `AUTHORIZED_BUYERS_BEARER_TOKEN=...`

---

## Troubleshooting

### "Missing authentication" Error
- Make sure you've set either `AUTHORIZED_BUYERS_SAPISIDHASH` + `AUTHORIZED_BUYERS_COOKIES` OR `AUTHORIZED_BUYERS_BEARER_TOKEN`

### "401 Unauthorized" Error
- Your credentials have expired (happens every ~60 minutes)
- Copy fresh values from Chrome DevTools and update your `.env` file

### "403 Forbidden" Error
- Verify API key is correct
- Check that tokens are not expired
- Ensure account has access to Authorized Buyers

### Cookie String Too Long?
- That's normal! The cookie string can be 2000+ characters
- Make sure to copy the entire string, including all cookies separated by `; `

## Pro Tip: Using Chrome's "Copy as cURL"

1. Right-click the `inventoryViews:search` request
2. Select **Copy** → **Copy as cURL**
3. Paste into a text editor
4. Extract:
   - `-H 'authorization: SAPISIDHASH ...'` → `AUTHORIZED_BUYERS_SAPISIDHASH`
   - `-H 'cookie: ...'` → `AUTHORIZED_BUYERS_COOKIES`
