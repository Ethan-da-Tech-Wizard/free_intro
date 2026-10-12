# Validation record

## Isolated full rehearsal — free_intro_1, September 24, 2026

The current copy's evidence is in [the rehearsal report](../AUDIT.html) and [its findings](../audit/FINDINGS.md). The earlier implementation checks below are preserved as history.

The rehearsal executed 82 browser exercises across all eight workflows, followed by four document retests after corrections. All 24 manual forms were filled and saved. The corrected backend suite passed 20 tests. Source cleanup warnings, supported PDF character encoding, intake draft instructions, the specific OCR correction, and static JSON evidence downloads were fixed in this copy. Fresh public Google and historical OpenF1 fetches succeeded; a real one-minute scheduled pull ran and was then stopped.

The book's stop, backup, rename, extract, and restart sequence ran against this copy. All 25 restored databases matched the backup byte for byte; saved record and run identities survived restart. The original workspace's dashboard still matches its pre-rehearsal snapshot.

After those reset and recovery lessons, all 24 apps were populated for presentation with 126 saved records. The report links those records, 218 rehearsal captures, 134 gallery captures, exact checklist text, downloads, and recorded commands. The current operator book has 360 checks; the conversation book has 252. Native desktop gestures, spoken learning/readiness checks, and owner conversations are labelled separately and are not asserted as completed interviews or physical GUI clicks.

Current proof files: `audit/summary.json`, `audit/final-state/manifest.json`, `audit/lifecycle/proof.json`, `audit/backend-tests-after-fixes.log`, `audit/reader-tests-after-report.log`, and `audit/report-verification/result.json`.

## Earlier implementation verification

Verified on the presenter's machine, 2026-09-23 (America/Phoenix). UTC source and screenshot timestamps may fall on September 24.

| Check | Result |
| --- | --- |
| Backend/operations suite | 17 tests passed, 5.394 seconds in the final backend run. Temporary HTTP services and independent SQLite stores. |
| Eight browser workflows | Each completed three destination writes and read-backs. Six real HTTP trace steps per ordinary intake. |
| Dirty spreadsheet through the browser | Header detection, normalization, mapping, populated intake, and field preview passed. |
| Mobile and browser runtime | 390px overview/navigation passed without horizontal overflow; no JavaScript runtime errors. |
| Public Google Sheet | HTTP 200; 30 rows and six columns. Mapped row reached registration, session, and badge stores. |
| Historical OpenF1 | HTTP 200 from drivers, laps, and sessions. Derived report reached ledger, calendar, and local briefing stores. |
| Actual scheduled refresh | The one-minute timer fetched the public Google Sheet and saved all 30 source rows in each of three workplaces. The timer was then disabled. |
| Real process restart | Same saved IDs survived stopping/restarting Python; unfinished billing resumed without rewriting completed records. |
| Scan OCR | Form rasterized with Poppler, read with Tesseract, checked for extracted name and field labels. |
| Office interoperability | Generated XLSX opened and converted by actual headless LibreOffice in an isolated profile. |
| PDFs and calendars | Output PDF text parsed by Poppler; each captured destination's PDF downloaded; iCalendar UTC time and line folding checked. |
| Actual capture run | 134 screenshots across eight stories, with no browser runtime errors. |
| Evidence integrity | 134 manifest entries, 134 matching SHA-256 file hashes. |
| Archi assets | Eight scenarios and ten editable views validated; all ten PNGs exported by the existing Archi executable. |

Backend coverage includes manual isolation, exact propagation, duplicate input, receipt identity, unique-item sales, invoice arithmetic, return visits, concurrent slot conflicts, waitlists/check-in, review holds, mismatched invoices, 403/503 recovery, archived-run protection, invalid sources, local authorization, and cross-origin rejection. An intervening destination edit is detected and is not reported as verified.

The capture script types and saves all 24 manual forms, resets the owned stores, runs each single intake, opens each saved destination, exercises failure/recovery, and records selected business follow-ups. Typing is scripted for repeatability; the captures do not establish human speed or savings.

Provider proof: `fixtures/public/verification.json`. Timer proof: `fixtures/public/schedule-verification.json`. Screenshots and exact timestamps: `evidence/manifest.json`.

No paid API key, subscription, AI service, or trial credit was used. Existing hardware, power, and internet are assumed. Python's standard library supplies the application runtime; Node/Playwright are development tools. Captures occupy approximately 22 MB. Runtime state varies with use.

The app consists of synthetic local workplaces and verified read-only public sources. Research is not evidence of connecting commercial vendors. [IMPLEMENTATION.md](IMPLEMENTATION.md) documents file limits, review requirements, and deployment boundaries.

## Checklist books and tutorial verification — 2026-09-24

Delivered two offline/web books: **The Works** (27 chapters, 359 checkpoints) and **The Business Owner Playbook** (23 chapters, 252 checkpoints). The field-reference tables are generated from the actual application contracts. Complete Markdown and blank printable PDF editions accompany the HTML reader; 26 practice files supply every lesson's input without a customer account.

`node tests/books.mjs` passed using independent temporary application databases and fresh browser contexts. It checked both books over `file://` and HTTP: chapter navigation, all-chapter mode, search/no-results, saved checks and notes after reload, progress export/import, rejection of another book's progress file, mobile navigation/overflow, and complete print visibility. It then performed all 32 manual HVAC field entries and verified three saved records and PDFs, followed the automatic HVAC intake/completion/$250 invoice/second-job lesson, and exercised the event capacity-one waitlist, rejected check-in, deliberate capacity-two correction, and successful check-in. No browser runtime errors occurred. Test checks wait for the submitted follow-up's response and closed dialog before inspecting its result.

The launcher reused the existing workspace process, stopped it gracefully, and restarted it. The existing 58 destination records, run identifiers/statuses, and dashboard counters were preserved. The schedule remained off. All three guide pages, the reader script, and both PDFs returned HTTP 200 from the normal service after restart.

Evidence is in [books/verification/result.json](../books/verification/result.json), [launcher.json](../books/verification/launcher.json), and the desktop/mobile reader screenshots in that folder. `node scripts/print_books.mjs` creates blank PDFs in fresh browser contexts, without study notes. The prepared editions have 72 and 51 A4 pages respectively, with contents and page numbers. PDF text and selected rendered pages were inspected. Reader progress is browser-local and separate from the application's SQLite state; its export is an explicit JSON backup.

Provider documentation links in the business guide were reopened on September 24. Candidate products remain research candidates. The original public-source and business-engine verification above was not represented as a fresh full rerun for this documentation task.
