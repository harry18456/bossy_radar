# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Chrome/Edge extension (Manifest V3) that displays labor violations, environmental violations, and salary data from Bossy Radar when browsing 104.com.tw job/company pages. Zero-build, plain JavaScript — no bundler, no package.json, no npm.

## Development

Load as an unpacked extension:
1. Open `chrome://extensions/` (or `edge://extensions/`)
2. Enable Developer Mode
3. "Load unpacked" → select the `extension/` folder
4. Browse any company or job page on 104.com.tw

There are no build steps, linting, or tests. Changes to JS/CSS take effect after reloading the extension.

## Architecture

Four files, each running in a different execution context:

```
content-scripts/injector.js     content-scripts/interceptor.js     content-scripts/main.js     background/service-worker.js
(isolated world,                 (main world,                        (isolated world,             (background)
 document_start)                  injected by injector)               document_idle)
```

### Cross-world communication (MV3 constraint)

Content scripts run in an isolated world and cannot access page JS globals. The workaround:

1. `injector.js` injects `interceptor.js` into the page's main world via a `<script>` tag
2. `interceptor.js` monkey-patches `window.fetch` and `XMLHttpRequest.prototype.open` to capture `custNo` from 104's API request URLs **and response bodies**; it also scans inline HTML on load
3. It bridges back to the isolated world via two channels:
   - DOM attribute: `document.documentElement.setAttribute('data-bossy-tax-id', taxId)`
   - CustomEvent: `window.dispatchEvent(new CustomEvent('bossy-radar-tax-id', ...))`
4. `main.js` reads the DOM attribute and listens for the event

**Important guard**: `interceptor.js` sets `dispatched = true` after the first custNo is found — subsequent API calls (e.g. similar-company lists) cannot override the detected tax ID.

### CORS bypass

Content scripts on 104.com.tw cannot fetch from bossy.eraser.tw. All Bossy Radar data requests go through `service-worker.js` via `chrome.runtime.sendMessage`:
- `GET_CATALOG` — fetches `/data/company-catalog.json`, cached in `chrome.storage.local` with 24h TTL (cache key: `bossy_radar_catalog_v2`)
- `GET_COMPANY` — fetches `/data/companies/{code}.json` per page view

**Exception**: `fetchTaxIdBySlug()` in `main.js` fetches 104's own APIs directly (same-origin, no CORS issue) to resolve a company slug to its tax ID.

### Company matching (priority order)

1. **Tax ID** (`tax_id`) — extracted from 104 API's `custNo` param (first 8 digits); once matched via tax ID, cannot be overridden
2. **Exact name** (`name`) — from DOM `h1` or `og:title` meta tag
3. **Split name** (`name_split`) — handles 104's `Brand_FullCompanyName` format (split on `_`)

For job pages where interceptor hasn't yet captured a custNo, `main.js` attempts `fetchTaxIdBySlug()` which hits `/company/ajax/content/{slug}` and `/company/ajax/summary/{slug}`, falling back to scraping the company page HTML.

### SPA handling

104.com.tw is a Vue SPA. `main.js` uses `MutationObserver` on `document.body` to detect navigation, with a 2-second content timer and 5-second absolute timeout before showing "not found".

### Site variants

- `www.104.com.tw` — standard site (company pages have `h1`, job pages use slug-based API fallback)
- `go.104.com.tw` — international talent site (no `h1`, parses `og:title`, `custno` is encrypted so only name matching works)

## Key conventions

- All CSS classes prefixed with `br-` and DOM IDs prefixed with `bossy-radar-` to avoid collisions with 104's styles
- Widget renders by rebuilding `innerHTML` from scratch (no incremental DOM mutation)
- Salary values from the API are in units of 千元 (thousands); divide by 10 to get 萬 (ten-thousands) for display
- Year values from the API are ROC calendar years (民國年); add 1911 to convert to CE
- Extension version is read at runtime via `chrome.runtime.getManifest().version` and displayed in the widget header
- When bumping version, update `manifest.json` only
