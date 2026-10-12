# Findings from the complete rehearsal

This is the isolated `free_intro_1` copy, served at http://127.0.0.1:8875. The original workspace uses 8765. Its application databases were not used for rehearsal mutations.

There is no credible guarantee that software has no possible bugs. This report records the paths actually exercised, the problems found, and the remaining human checks. A deliberately rejected booking, duplicate receipt, oversell, or unauthorized write is an expected business outcome, not a failed rehearsal.

## Issues found and corrected in this copy

### F01 — the tutorial described intake draft retention incorrectly

The operator book said navigating away before a mapping preview could discard fresh typing. The browser actually saves intake edits into its current tab's memory as the person types. I typed a new issue, changed views, returned, and confirmed it remained; a reload restored the sample. The copy's chapter 02 now describes the observed behavior. Saving a run remains distinct from saving a browser draft.

### F02 — source review missed some invalid email/date headings

The supplied law-office workbook's row 7 contained `missing-at-sign.example.invalid` under **CLIENT EMAIL** and `03/04/26` under **APPOINTMENT**, yet the source inspector labelled it ready. Downstream validation still rejected the invalid business input, but the source's readiness label was misleading. The sports template also needed its **DELIVERY ADDRESS** email recognized in context.

The cleaner now recognizes client email and appointment headings, and recognizes a delivery email only within the known sports header layout. An unrelated postal delivery-address column remains a postal value. Regression checks and actual browser inspections confirm the email/date review warnings before submission. See `source-review-fixes/` and `backend-tests-after-fixes.log`.

### F03 — PDF font encoding altered supported characters

The generated PDF used a standard Helvetica font without declaring its encoding. A supplied middle dot was extracted as a bullet; accented characters were also vulnerable to incorrect decoding. The PDF writer now declares WinAnsi encoding and writes matching CP1252 bytes. Actual Poppler extraction verifies `Outdoor condenser · Unit A`, `Repair café`, and `Renée Example`.

This fixes the tested Western character set. The lightweight PDF writer is not a universal font/Unicode document engine. It still requires an appropriate font/renderer for unsupported scripts; that capability is not claimed by this demo.

### F04 — OCR needed a concrete correction in the practice lesson

The initial scan produced an asterisk where the original equipment description had a middle dot. After correcting the PDF encoding and regenerating the scan, OCR produced a hyphen there. This is an extraction limitation covered by human review, not evidence that the source text really contained the substitute character.

I compared the fields to the known original, corrected **Equipment** to `Outdoor condenser · Unit A` in the intake, recorded the review, and verified all three saved destinations. Chapter 09 now gives this exact correction instead of leaving the learner to discover it halfway through. The normalized phone preserves all digits and does not need to be changed back for the exercise.

### F05 — static JSON evidence links failed through the server

The final report check followed the evidence links over HTTP and caught a 422 response: `Object of type bytes is not JSON serializable`. Files opened correctly from disk, but the response helper tried to JSON-encode already serialized JSON file bytes. The same defect affected the gallery's **Inspect capture metadata and hashes** link.

The response helper now sends JSON file bytes unchanged while continuing to serialize API objects normally. A regression test downloads the scenario catalog and gallery manifest over actual HTTP, checks their JSON content type, and compares the exact response bytes with the files. The report verification also follows its JSON evidence downloads through the running service. The final backend suite has 20 passing tests.

## Rehearsal harness corrections

The first browser harness used an exact accessibility-name match for **Under the hood**; the tab also contains a **TECH** badge. The selector was corrected, and the complete 82-exercise browser pass succeeded. This was a harness selector problem, not a broken navigation link. The original failed attempt remains in `attempts/`.

An initial file assertion assumed every business's second generated row must be invalid. Retail, seller, and property examples can contain valid second rows. The assertion now checks the relevant email/date fixtures and preserves valid rows. A separate browser verification was also retried after waiting for the planned restart to finish; requesting a page during a deliberate shutdown correctly returned connection refused.

The report verifier was corrected to wait for hash navigation and a painted frame before checking/capturing the selected view. An overbroad PDF assertion expected the operator book's absolute startup path to appear in the conversation book too; each edition is now checked against its own contents. The earlier report-check logs remain in `audit/report-verification-*.log`. Those harness errors are separate from the genuine static-JSON defect above.

## What was exercised

- All 24 manual workplace forms: every specified input filled, saved, retrieved, and checked; each workplace document downloaded.
- One-time intake mapping, three actual API saves/read-backs, and all eight business workflows.
- HVAC $250 completion, duplicate completion, and an additional job for the same customer.
- Spreadsheet header cleanup, bad-row correction, duplicates, batch holds, and actual XLSX upload.
- Text PDF extraction and scanned-image OCR, including explicit correction against the original.
- Fresh public Google CSV and OpenF1 historical requests, mapping, documents, and labelled offline replays.
- An actual one-minute scheduled Google pull, followed by stopping the schedule.
- Legal review hold, clinic booking collision and correction, inventory receipt replay/new delivery/conflict, unique-item sale/oversell rejection, invoice-reference/amount holds, and capacity/waitlist/check-in rules.
- Real 403 and 503 writes, partial state, restoration, and resumed jobs that retain the first two saved IDs/revisions.
- PDF, XLSX, CSV, ICS, and evidence ZIP outputs; regenerated gallery of 134 actual captures.
- All eight workbooks opened by actual LibreOffice; all ten Archi views loaded/rendered by the existing executable.
- Start, reuse, stop, foreground launch/SIGINT, expected port collision, alternative ports, backup, rename, extraction, and restart. All 25 database files matched byte-for-byte immediately after restoring the backup; saved record/run identities survived restart.
- File and web book readers, mobile layout, search, notes, checkmarks, progress export/import, and printable documents.

## Human boundaries that remain visible

Physical KRunner shortcuts, Dolphin double-click behavior, KDE trust prompts, and native Save As/print-dialog choices cannot be claimed as clicked by this browser/terminal audit. The named executables, paths, actual file operations, native document tools, and browser actions were exercised; the report marks OS interactions separately.

The conversation checklist contains real questions to ask an owner, spoken rehearsal, listening, approvals, and self-assessments. No business owner was interviewed and no messages were sent. Written scripts and evidence were prepared; those tasks are not falsely ticked as completed meetings. Vendor approval, private-account access, live marketplace publication, payments, and real medical/legal operations remain outside the implemented local demo.

The original public sources were reachable during this run. That is observed availability, not a promise that a third-party service will always respond. Recorded replays remain clearly labelled alternatives.

The terminal executor's login-shell route also exposed an existing syntax error in the user's `.bash_profile` at line 10. The documented project commands were verified in a non-login shell. This audit does not modify that unrelated personal shell file or claim to have repaired it.
