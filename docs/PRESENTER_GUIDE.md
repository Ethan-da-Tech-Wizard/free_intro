# Presenting Relayworks

For the complete beginner walkthrough, open [The Works](../THE_WORKS.html). For discovery questions, detailed business/app talking points, and meeting checklists, open [The Business Owner Playbook](../BUSINESS_PLAYBOOK.html). The [library](../START_HERE.html) links both books and their PDFs. This older guide remains a short presentation route.

Start `python3 app/server.py`, then open http://127.0.0.1:8765. The core demonstration works without accounts or internet. Live source buttons use the network; recorded examples remain available offline.

## The seven-minute centerpiece

1. Open **HVAC & field service → Do it manually**. Open Customer Profiles, Dispatch Desk, and Billing Desk in separate tabs.
2. Type and save the source facts in each app. The eight common customer facts are entered three times. The forms contain 32 fields in total, including job-specific facts; the single intake contains 15. These are interface counts, not a measured human speedup.
3. Use **Before & after** to show retained manual-entry screenshots when you want a shorter presentation.
4. Return and **Reset workplaces**. The confirmation identifies exactly what is cleared. Old screenshots and run traces remain.
5. Open **Automate it**. **Preview field mapping** exposes destination field names. **Populate all three apps** starts the real transfer.
6. Open each saved record. Point to its own ID and values. Customer Profiles retains the service reference; dispatch owns the reservation; billing owns the draft. Download the populated work order or invoice from its workplace.
7. Choose **Complete the visit**. The defaults calculate $95 diagnostic fee + 1.5 hours × $80/hour + $35 parts = **$250.00**. Apply the event and inspect the updated draft. Nothing is charged or emailed.
8. For technical viewers, expand a POST and its following GET in **Under the hood**. The service retrieves the saved record, compares values, and keeps the request, response, status, duration, and ID.

For another visit, keep the customer reference, choose a new job reference and unoccupied slot, and run again. The customer ID is reused while dispatch and billing create records for the new job.

## “Even this ugly spreadsheet?”

1. In **Sources & connections**, download XLSX or CSV for a business. These generated files contain banners, blanks, padded text, duplicate rows, and relevant invalid fields.
2. Click **Clean & map**. Compare untouched rows against cleaned values, header detection, duplicate flags, and review warnings. This is real parser output.
3. Choose a row and review column mappings. **Use this row in the intake** fills the shared intake. Unmapped values are labelled demo defaults.
4. Run the valid row. Try the malformed row, correct its email/date, confirm review, and run. A checkbox does not bypass required-field validation.
5. **Populate all ready rows** submits valid nonduplicate rows and reports those held. Run history shows each job's actual result.

Mappings are remembered for the same workflow and columns. The XLSX reader uses the first worksheet, preserves text IDs, and reads cached formula values rather than calculating formulas. Supported formats and limits are in the implementation document.

## Google Sheets with no key to provide

1. Open Google's original public sample using the Sources link, then click **Pull from Google Sheets**.
2. Show the export URL, HTTP response, retrieval time, six columns, and 30 returned rows from the verified sample.
3. In Community & events, `Student Name` maps to attendee name and `Major` to session. Missing emails and registration references are explicitly synthetic values.
4. Send one row or all ready rows. Open the registration roster, session board, and badge app. Full sessions become waitlisted.
5. Enable a schedule to re-read every minute, five minutes, or fifteen minutes. The server must stay running. Unchanged input reuses runs. Stop scheduling after presenting it.

The public classroom sample is Google's developer example. The ugly workbooks are separately generated here. Other public/published Sheet URLs work; private OAuth is not implemented. Row-based generated IDs suit the fixed sample; changing business sheets should map stable IDs.

## Real sports data

**Fetch historical F1 data** makes three OpenF1 requests for driver 1, session 9158, and its laps. The importer computes the minimum positive recorded lap duration and counts the returned lap records. Historical event date and retrieval time are shown separately.

The recipient is synthetic; driver/session/lap facts come from the provider. Open the source ledger, schedule, and local briefing. An aware timestamp is converted to the selected display zone. Download the actual `.ics` file; its one-hour demonstration duration is not the provider's official session duration.

Historical access is free and needs no key. Paid live telemetry is excluded. Scheduled refreshes re-read this fixed historical example, rather than claiming current race updates.

## Other stories

| Story | Demonstrate | Exception or next step |
| --- | --- | --- |
| Law office | Intake → matter → populated client packet → task | Seed a possible party match with “Demonstrate a review hold.” Preview stops until the reviewer records a decision. |
| Clinic | Synthetic registration → appointment → packet | Try a conflicting appointment. Choose a different slot in the intake and run again. |
| Retail | Counted receipt → stock → storefront availability | Replay returns the existing run. A new receipt adds stock; one receipt cannot add stock twice. |
| Seller | Item details → draft listing → sale paperwork | Record a sale, inspect stock 0 and the packing slip. A second distinct sale of the unique item is rejected. |
| Property | Repair request → work order → owner statement | Match invoice to job. Incorrect job references or amounts above the estimate are held for correction. |
| Events | Registration → seat → badge | Lower capacity and add registrations to show a waitlist. Only a reserved attendee can check in. |

## Permission loss and recovery

Reset the workflow, revoke access to its third destination in **Under the hood**, then submit new input. The first two apps save; the third returns a real 403. Taking it offline produces a 503 instead. Restore access/service and **Resume from saved step**. Earlier IDs and revisions remain; unfinished transfers execute. The trace contains both the failure and successful retry.

This is a server-enforced local grant, not a claim that an external vendor approved access. Business apps are purpose-built local workplaces. Reports stay local; medical or legal decisions are not automated.

Run history preserves execution snapshots even if current records later change. Reset archives old runs. An evidence ZIP contains the current run JSON, PDF packet, diagrams, and retained screenshots. Screenshot timestamps distinguish the recorded demonstration from the current run.

## Presentation preparation

Start the server, check the intended live source or select its recorded replay, stop leftover schedules, and reset the workflow you will type through. The gallery lets you shorten typing without presenting a screenshot as live execution. No secret keys or real customer data are needed.
