# Authentication Architecture: SAPISIDHASH Session Tokens

**Last Updated:** 2026-01-20  
**Project:** `bedrock-us-east`  
**Service:** Authorized Buyers Internal API

---

## Overview

This tool uses **SAPISIDHASH authentication** with browser session cookies. Tokens must be manually extracted from Chrome DevTools and added to your `.env` file.

**Why Manual Tokens?**
- The internal API endpoint (`adexchangebuyer.clients6.google.com`) requires browser session cookies
- Service account Bearer tokens do NOT work (endpoint returns 404)
- Tokens expire every ~60 minutes and must be refreshed manually

---

## Step-by-Step: Getting Session Tokens

### 1. Open Chrome DevTools

1. Open **Chrome** browser
2. Navigate to **Authorized Buyers UI** (realtimebidding.google.com)
3. Press **F12** (or right-click → **Inspect**)
4. Go to the **Network** tab

### 2. Trigger the API Request

1. Navigate to the **inventory views** page in Authorized Buyers UI
2. The page will make an API request automatically
3. Look for a request named `inventoryViews:search` in the Network tab
4. If you don't see it, refresh the page or interact with the inventory filters

### 3. Extract SAPISIDHASH

1. Click on the `inventoryViews:search` request
2. Go to the **Headers** tab
3. Scroll down to **Request Headers**
4. Find the `authorization` header
5. You'll see something like:
   ```
   SAPISIDHASH 1768473013198_6ae15f8eef6e2ee384572a5d2c288471a68b7427
   ```
6. **Copy the entire value** (including "SAPISIDHASH " prefix is fine)
7. This is your `AUTHORIZED_BUYERS_SAPISIDHASH` value

### 4. Extract Cookies

1. Still in the **Headers** tab → **Request Headers**
2. Find the `cookie` header
3. Right-click on the cookie value → **Copy value**
4. The cookie string is **very long** (2000+ characters)
5. It contains many cookies separated by `; `
6. **Copy the entire string** - make sure you get all of it
7. This is your `AUTHORIZED_BUYERS_COOKIES` value

### 5. Update .env File

Open your `.env` file and add/update these values:

```env
AUTHORIZED_BUYERS_ACCOUNT_ID=7287432622
AUTHORIZED_BUYERS_API_KEY=AIzaSyDntWfIQs0iyimIUm1GTOWjx5fJL8YdKTE
AUTHORIZED_BUYERS_SAPISIDHASH=1768473013198_6ae15f8eef6e2ee384572a5d2c288471a68b7427
AUTHORIZED_BUYERS_COOKIES=XSRF-TOKEN=AFCo3MCuMbW6uaZMCicHPbOpbz17ROkt9A:1761828754296; S=billing-ui-v3=f8rXrlcuAcw8aTK1JMUJY84Pd35HLSwzLPltrv4J49o; ... (rest of cookies)
```

**Important Notes:**
- Keep the cookie string on **one line** (don't break it across multiple lines)
- Include **all cookies** in the cookie string
- The SAPISIDHASH can include or exclude the "SAPISIDHASH " prefix (both work)

---

## Token Expiration

**Tokens expire every ~60 minutes.**

When you get a **401 Unauthorized** error:
1. Go back to Chrome DevTools
2. Extract fresh tokens following steps 2-4 above
3. Update your `.env` file with the new values
4. Run the script again

---

## Troubleshooting

### "Missing authentication" Error

- Make sure both `AUTHORIZED_BUYERS_SAPISIDHASH` and `AUTHORIZED_BUYERS_COOKIES` are set in `.env`
- Check that values are not empty

### "401 Unauthorized" Error

- Tokens have expired (~60 minutes)
- Extract fresh tokens from Chrome DevTools
- Update `.env` file

### "403 Forbidden" Error

- Verify `AUTHORIZED_BUYERS_API_KEY` is correct
- Check that tokens are not expired
- Ensure account has access to Authorized Buyers

### Cookie String Too Long?

- That's normal! Cookie strings are 2000+ characters
- Make sure you copied the **entire** cookie string
- Don't break it across multiple lines in `.env`

### Can't Find the Request?

- Make sure you're on the inventory views page
- Refresh the page
- Try interacting with filters/search
- Check Network tab filter is set to "All" (not just XHR)

---

## Pro Tip: Using Chrome's "Copy as cURL"

1. Right-click the `inventoryViews:search` request in Network tab
2. Select **Copy** → **Copy as cURL**
3. Paste into a text editor
4. Extract:
   - `-H 'authorization: SAPISIDHASH ...'` → `AUTHORIZED_BUYERS_SAPISIDHASH`
   - `-H 'cookie: ...'` → `AUTHORIZED_BUYERS_COOKIES`

---

## Why This Method?

The internal API endpoint (`adexchangebuyer.clients6.google.com`) requires:
- Browser session cookies (cannot be generated programmatically)
- SAPISIDHASH authorization header (tied to browser session)

**Service account Bearer tokens do NOT work** - the endpoint returns `404 Method not found` when using OAuth2 tokens.

This is the **only way** to access forecast/breakdown discovery data, which is not available in the public Authorized Buyers Marketplace API.

---

## Quick Reference

| Component | Value |
| --- | --- |
| **Auth Method** | SAPISIDHASH + Cookies |
| **Token Source** | Chrome DevTools (Network tab) |
| **Token Expiry** | ~60 minutes |
| **API Endpoint** | `adexchangebuyer.clients6.google.com//v1internal/` |
| **Request Name** | `inventoryViews:search` |
| **Headers Needed** | `authorization` (SAPISIDHASH) and `cookie` |

---

**Related Documentation:**
- [QUICK_START.md](../QUICK_START.md) - Quick start guide
- [README.md](../README.md) - Main project documentation
