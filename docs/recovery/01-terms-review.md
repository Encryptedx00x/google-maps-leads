# Recovery checkpoint 01 — Google Maps Leads: terms review

- Checkout cloned because no existing directory was found: `C:\Users\Encryptedx\Desktop\google-maps-leads`.
- Branch: `codex/recovery`; starting commit `bd5ef66`.
- Inspected the complete small project (`README.md`, `requirements.txt`, `scraper_google_maps.py`). The script accesses the Google Maps UI using Selenium and copies business names, phones, types, and addresses to an XLSX file. It also starts prompts and a browser at module import time.
- Current Google Maps End User Additional Terms prohibit copying content and bulk feeds. Google Maps Platform terms separately prohibit scraping/extracting content and copying/saving business names and addresses outside the services. Given the product's stated output (an exported lead spreadsheet), a small live search is not a compliant validation path. No Google Maps request or browser session was started.
- The README now marks collection as pending and directs future work to a data source whose license permits extraction and export. An official API is not presumed to authorize spreadsheet export.

Status: **PENDENTE** until a compliant acquisition source is selected. No Selenium selector, rate-limit, pagination, or live-search changes were made because that would operationalize the disallowed data extraction. Offline regression tests and workbook safety validation remain pending for a replacement permitted input path.

Sources reviewed 2026-11-04:
- https://www.google.com/help/terms_maps/ (end-user terms; copying and mass-download restrictions)
- https://cloud.google.com/maps-platform/terms (Platform section 3.2.3(a), no scraping/copying business names and addresses)
