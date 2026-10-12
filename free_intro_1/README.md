# Relayworks

This is **free_intro_1**, the independently rehearsed copy. Start with [the findings and recorded walkthrough](AUDIT.html), or open **http://127.0.0.1:8875/AUDIT.html** while its server is running. The report links the populated apps, recorded steps, both exact checklists, fixes, and test evidence. It separates verified software actions from physical desktop and presenter actions.

To reopen this copy after a restart:

```sh
cd /home/ethan/pg/free_intro/free_intro_1
python3 scripts/launch.py
```

Choose **Rehearsal findings** in the sidebar. The two books also link to the report. Existing saved records survive a restart. The rehearsal finished with all 24 apps populated and the source timer off. Rehearsal and capture scripts reset this copy's practice workplaces; the report itself is read-only.

A working, free automation showcase: eight business workflows, 24 clickable workplace apps, messy spreadsheet and document imports, real Google Sheets and OpenF1 reads, and actual before/after screenshots.

## Start with the two checklist books

Open [START_HERE.html](START_HERE.html) in your browser, or use **Guides & checklists** inside the demo. The books also work as files while the server is stopped.

- [The Works](THE_WORKS.html): 27 chapters, exact Dolphin/Kitty startup steps, every manual and automated workflow, source imports, recovery, diagrams, backups, and all 24 apps' field references. [Printable PDF](books/THE_WORKS.pdf).
- [The Business Owner Playbook](BUSINESS_PLAYBOOK.html): 23 chapters of discovery questions, demonstrations, talking points for each app/tool/process, cost and capacity explanations, objections, SDLC responsibilities, and meeting worksheets. [Printable PDF](books/BUSINESS_PLAYBOOK.pdf).

Both have a table of contents, search, saved checkmarks and notes, progress export/import, and printing. Progress belongs to the browser/address used; export it before switching browsers. Blank PDF and complete Markdown editions are in `books/`. Actual CSV, XLSX, PDF, and scanned-image practice inputs are ready in `practice_files/`.

Double-click `START_RELAYWORKS.desktop` from Dolphin, or run `python3 scripts/launch.py` from this project folder. The launcher opens the browser and reuses the existing normal instance without resetting records. `--status` checks it; `--stop` gracefully stops only this workspace's normal server. The Works chapter 01 explains desktop execution prompts and the terminal alternative.

## Run it

```sh
python3 app/server.py
```

Open **http://127.0.0.1:8875**. `npm start` runs the same command. Python 3.10+ with its standard library is the only application runtime dependency. The portal uses port 8875 and the authenticated workplace API uses 8876; both bind to loopback.

The existing machine has Poppler and Tesseract for PDF text extraction and scan OCR. Without those optional system tools, CSV, Excel, public sources, generated documents, and manual entry still work; unavailable importers report what they need. No paid account, API key, AI service, subscription, trial credit, or runtime package download is required.

## Present it

Start with **HVAC & field service → Do it manually**. Type the customer facts into the three separate apps, reset the workplaces, then use **Automate it**. Open all three saved records. Complete the visit to update the invoice draft. In **Under the hood**, revoke access or take a destination offline, submit new input, restore access, and resume.

**Sources & connections** includes a public Google Sheet, historical F1 data, and generated ugly workbooks for every business. Imports show the untouched source, cleaned values, review flags, mappings, and labelled synthetic defaults. Retained provider responses can be replayed without internet; they are labelled recordings.

- [Presenter guide](docs/PRESENTER_GUIDE.md): presentation routes and recovery instructions.
- [Implementation and acceptance](docs/IMPLEMENTATION.md): running structure, checks, boundaries, and scaling.
- [Team charter](TEAM_CHARTER.md): senior engineering roles and SDLC responsibilities.
- [Eight workflows](docs/WORKFLOW_CATALOG.md): before/after structures, rules, and candidate tools.
- [Research and costs](docs/RESEARCH.md): official sources, provider limits, and access requirements.
- [Evidence manifest](evidence/manifest.json): screenshot URLs, timestamps, record IDs, and hashes.
- [Editable flowcharts](diagrams/showcase.archi.json): ten views for the existing Archi app.

## What is connected

Google's public sample Sheet is fetched over HTTPS as CSV. OpenF1 supplies historical session, driver, and lap data. Poppler extracts PDF text, Tesseract reads scans, and Python reads/writes CSV/XLSX and generates PDFs and calendar files. The browser operates real local HTTP services and 24 independent SQLite stores.

The business apps are fictional demo workplaces. OpenEMR, ERPNext, Baserow, docassemble, WooCommerce, and eBay are researched candidates; this project does not claim to have connected those vendors or obtained their approval. Private Google authorization, internet email delivery, real payments, shipping labels, and production hosting are outside the local presentation.

## Reproduce the checks and evidence

```sh
python3 -m unittest discover -s tests -v
npm install
npx playwright install chromium
npm run test:browser
node scripts/verify_sources.mjs
npm run capture
```

Only the browser development tools need npm. Start the demo before browser/source checks. Integration tests use temporary databases and ports. Browser checks and capture runs reset only the demonstration's own records. Captures retain screenshots and history; no external data is deleted. Source verification makes read-only public requests and saves labelled recordings under `fixtures/public/`.

`node scripts/verify_schedule.mjs` also checks one actual one-minute Google Sheets timer and disables it afterward. The verified run populated 30 rows in each event app. [Validation record](docs/VALIDATION.md) lists the executed checks.

For an isolated second instance:

```sh
python3 app/server.py --port 8865 --workplace-port 8866 --data-dir /tmp/relayworks-practice
```

**Reset workplaces** clears that scenario's 3 local databases and archives previous runs. Persistent state lives in `runtime/`. Restarting retains records and traces and marks interrupted jobs ready to resume. Keep the server running for scheduled pulls; scheduling is opt-in.

Regenerate diagrams with `python3 scripts/build_planning_assets.py --archi /home/ethan/pg/archi/build/archi`. This replaces generated diagrams and the catalog; preserve hand-edited Archi boards separately.

Book maintenance: edit `docs/THE_WORKS.md` or `docs/BUSINESS_PLAYBOOK.md`, then run `python3 scripts/build_books.py` and `node scripts/print_books.mjs`. The builder expands the field reference from `app/config.py`; editable sources contain these expansion markers, while `books/*.md` contain the complete expanded text. Reader styling/behavior live in `web/books.css` and `web/books.js`. `node tests/books.mjs` verifies the file/web readers and selected step-by-step lessons using isolated temporary application stores and browser profiles; it does not reset your normal demo. `python3 scripts/make_practice_files.py` regenerates the supplied practice inputs.
