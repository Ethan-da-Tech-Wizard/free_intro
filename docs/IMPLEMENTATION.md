# Implementation and acceptance

The running product is the local Relayworks app. Vendor research describes possible real-world integrations separately from the connected demonstration.

| Component | Implementation |
| --- | --- |
| Presentation | Local HTML/CSS/JavaScript; responsive overview, eight workflows, 24 workplace forms, source inspector, history, evidence. |
| Portal | Python threaded HTTP server on 127.0.0.1:8765; intake validation and presenter API. |
| Orchestrator | Three workers; SQLite persists inputs, provenance, events, request traces, verified IDs, sources, mappings, and the optional schedule. |
| Workplace API | Second listener on 127.0.0.1:8766, with a generated local bearer grant kept out of the browser. |
| Workplace storage | 24 independent SQLite files, each owning its records, revisions, operations, and domain reservations/events. |
| Files | Poppler extraction, Tesseract OCR, CSV/XLSX parsing, PDF/XLSX generation, and calendar exports. |
| Public sources | Real HTTPS Google CSV exports and historical OpenF1 JSON; original values and fetch metadata retained. |
| Evidence | Actual Chromium captures with hashes, timestamps, URLs, and IDs; ten editable Archi views. |

Writes use `POST /v1/{scenario}-{0|1|2}/records`, followed by `GET /v1/{app}/records/{id}` and payload comparison. Destination fields have explicit mappings. The three views do not substitute a shared browser object for independent records.

## Acceptance behavior

- Eight workflows each save and read back three independent records. Manual entry in one app leaves the others alone.
- Identical inputs reuse a run. Destination operation IDs protect repeated writes. Receipt events cannot double-add stock; unique items cannot sell twice; appointment reservations serialize.
- Restored 403/503 failures resume unfinished steps and preserve completed IDs and revisions.
- Completion updates the existing invoice with decimal arithmetic. An existing customer can receive another service visit.
- Legal review, appointment conflicts, event capacity/check-in, and invoice matching are visible rules.
- Messy workbooks preserve originals, detect headers/blanks/duplicates, normalize values, and hold ambiguous data. Mapped inputs still require validation.
- Actual PDFs are extracted and generated; exported PDF text is checked. XLSX contains spreadsheet XML; calendar files contain actual iCalendar data.
- Reset affects one scenario, archives history, and changes deduplication generation. Restart retains state and marks interrupted jobs resumable.
- Host/Origin checks reject cross-origin writes. The workplace listener rejects missing authorization. Public-source hosts are restricted. CSV exports neutralize formula prefixes.

Run `python3 -m unittest discover -s tests -v` for temporary-server integration tests. `npm run test:browser` exercises the UI, mapping, mobile layout, and browser errors. `node scripts/verify_sources.mjs` checks actual public reads and propagation. `npm run capture` fills the forms, saves them, executes jobs, triggers failures, resumes, and checks populated PDFs.

The final execution record is [VALIDATION.md](VALIDATION.md). Provider proof is in `fixtures/public/verification.json`; screenshot metadata is in `evidence/manifest.json`.

## Supported scope and scaling

Parsing uses explicit schemas and rules. Uploads are capped at 8 MB; expanded workbooks at 25 MB. CSV/XLSX use up to 1,001 rows, XLSX's first worksheet and 80 columns. Scanned PDFs use their first three pages. Labelled forms are supported; arbitrary handwriting, encrypted files, complex layouts, `.xls`, macro execution, and formula calculation are not implemented.

Google public exports are supported; private OAuth and Sheets writeback are not. Missing IDs in the official sample use row numbers; a changing business sheet needs stable identifiers. Duplicate-row detection and input deduplication are not general entity resolution. Imported facts and synthetic defaults remain distinguishable.

Local API access grants are real enforced settings on the destination write path, not vendor approvals. The presenter can still read records to inspect a failure. No third-party business vendor credentials have been requested. Outputs remain local; the app does not deliver real email, submit legal filings, make medical decisions, publish listings, purchase labels, or charge payments.

Three workers and SQLite transactions suit a single-machine showcase. Cross-app operations are resumable sequences rather than distributed atomic transactions; earlier records remain visible during a later failure. Scheduling is opt-in, minimum 60 seconds, one configured public source, and up to 100 clean rows per tick. It runs only while the server runs. The app has no distributed broker, HA deployment, cross-process scheduler lock, automatic exponential retry, or production tenant access control. History grows in the local data directory.

Processing milliseconds are measured per run; they are not a guaranteed throughput or human time saving. A production deployment needs provider-aware quotas, bounded queues, retention, stable IDs, access control, and realistic load measurements. These are deployment requirements, not claimed implemented capacity.

## Code ownership

`app/config.py`: scenario contracts. `app/data_tools.py`: parsers and public sources. `app/engine.py`: validation, business rules, persistence, orchestration. `app/server.py`: HTTP surfaces and scheduling. `web/`: interface. `tests/`: acceptance checks. `scripts/`: source verification, capture, and Archi generation. `runtime/`: local state, excluded from source control.
