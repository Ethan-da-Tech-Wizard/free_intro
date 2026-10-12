# Real tools, access, costs, and evidence

Research date: 2026-09-23. Sources below are provider/project documentation. The delivered demo has verified real public Google Sheets and historical OpenF1 reads, and local Poppler/Tesseract document tools. The other business vendors below remain researched candidates, not connected installations or granted accounts. Local workplace examples are our own apps.

## Connections actually verified

- Google's [official Sheets quickstart](https://developers.google.com/workspace/sheets/api/quickstart/python) identifies the public sample used here. The demo reads its public CSV export (not the quickstart's private OAuth flow): HTTP 200, 30 rows, six columns, mapped into three event workplaces. No account or key was needed.
- [OpenF1](https://openf1.org/docs/) returned HTTP 200 for driver 1, session 9158, and lap data. The resulting driver report was saved into the source ledger, calendar, and local briefing app. Historical event time is distinguished from retrieval time.
- Reproducible provider request URLs, timestamps, source kinds, and destination IDs are retained in `fixtures/public/verification.json`. Offline recordings retain the original timestamp and are labelled replays.
- Poppler reads labelled PDF fields; Tesseract handles scans. CSV/XLSX processing, generated PDFs, independent SQLite stores, and calendar exports run locally. No paid AI service is involved.

## Sources and candidates

| ID | Verified capability and access | Free boundary relevant to this showcase | Primary sources |
| --- | --- | --- | --- |
| `libreoffice` | Office suite with spreadsheet and document tools. The generated XLSX was opened and converted by LibreOffice in the interoperability test. | Free and open-source software; local file processing needs no developer account. | [LibreOffice overview](https://www.libreoffice.org/) |
| `baserow` | REST database operations with tokens whose create/read/update/delete permissions can be set per table. | Free cloud plan: 3,000 rows and 2 GB per workspace in the reviewed documentation. Self-hosting is available; several advanced features are paid. | [API](https://baserow.io/user-docs/database-api), [plans](https://baserow.io/user-docs/pricing-plans) |
| `erpnext` | Frappe exposes document REST APIs with user permissions and API key/secret authentication. ERPNext documents maintenance visits and invoices, including carrying information forward from upstream records. | Open-source ERP software; managed hosting is a separate cost. Use an owned local installation for the no-subscription demonstration. | [REST API](https://docs.frappe.io/framework/user/en/api/rest), [maintenance visits](https://docs.frappe.io/erpnext/maintenance-visit), [invoices](https://docs.frappe.io/erpnext/sales-invoice), [pricing](https://frappe.io/erpnext/pricing) |
| `football` | football-data.org documents match and standings endpoints using an `X-Auth-Token` key. | The reviewed free plan has 12 competitions, delayed scores/schedules, and 10 calls/minute. Paid live-score and deeper-data options are outside the required $0 path. | [Pricing](https://www.football-data.org/pricing), [request examples](https://docs.football-data.org/general/v4/coding_client.html), [API policies](https://docs.football-data.org/general/v4/policies.html) |
| `openf1` | Unofficial F1 project providing session, driver, lap, and other data as JSON/CSV. | Historical data from 2023 onward is available without authentication. Real-time data requires a paid subscription and is excluded. | [OpenF1 documentation](https://openf1.org/docs/), [authentication](https://openf1.org/auth.html) |
| `balldontlie` | NBA API offering several categories of basketball data with API key authentication. | Free access covers teams, players, and games at 5 requests/minute. Player game statistics, injuries, and several advanced endpoints are paid. Its paid-tier trial requires a payment method; do not use that trial for this showcase. | [Account tiers and authentication](https://nba.balldontlie.io/) |
| `docassemble` | Free open-source guided interviews and document assembly, with an HTTP API for sessions and variables. API keys are created by users with the appropriate privileges. | Host locally; no paid document-automation platform is required. The interview and document templates still need to be authored for the scenario. | [Project](https://docassemble.org/), [API](https://docassemble.org/docs/api.html), [overview](https://docassemble.org/docs.html) |
| `openemr` | Free open-source medical/practice software. Standard REST APIs include demographics and appointment operations; OAuth registration, permissions, and TLS setup are required. Its FHIR API is a separate interface. | A local instance with synthetic data can demonstrate administration without a paid EHR account. Verify the deployed version's routes and scopes before choosing operations. | [Project](https://www.open-emr.org/), [API setup](https://github.com/openemr/openemr/blob/master/Documentation/api/README.md), [Standard API resources](https://github.com/openemr/openemr/blob/master/Documentation/api/STANDARD_API.md) |
| `woocommerce` | The core store provides REST APIs and event webhooks for resources such as products and orders. Webhooks support signature secrets and delivery logs. | The core plugin is free; a local WordPress installation avoids hosting fees. Paid extensions, payment processing, postage, and production transactions are not required. | [REST API](https://woocommerce.com/document/woocommerce-rest-api/), [webhooks](https://woocommerce.com/document/webhooks/) |
| `ebay` | A developer account provides separate application keys and sandbox test users. The sandbox uses fictional listings and money. | Developer membership is free. Account approval is needed; no approval has been requested or granted for this project. The provider explicitly says not to use its sandbox for load testing. | [Get started](https://developer.ebay.com/develop/guides/sell/get-started-with-ebay-apis), [sandbox and production](https://www.developer.ebay.com/api-docs/static/gs_understand-the-sandbox-and.html), [sandbox benefits](https://www.developer.ebay.com/api-docs/static/gs_sandbox-benefits.html), [test users](https://developer.ebay.com/api-docs/static/sandbox-test-users.html) |
| `nextcloud` | Documented WebDAV operations provide file upload, retrieval, folders, and related metadata. | Candidate local document destination; use the existing machine and test account access. Verify server/app packaging and authentication during setup. | [WebDAV operations](https://docs.nextcloud.com/server/stable/developer_manual/client_apis/WebDAV/basic.html), [client APIs](https://docs.nextcloud.com/server/stable/developer_manual/client_apis/index.html) |
| `mailpit` | Local SMTP test receiver with a browser interface and API for inspecting messages. | Captures demonstration messages locally; demonstrating internet email delivery is a different capability. | [Mailpit project](https://mailpit.axllent.org/) |

Additional candidates already documented in the team charter include Paperless-ngx for OCR/document management and Google Sheets for a free hosted spreadsheet integration within its current quota and pricing rules.

## What the access story should actually show

Different tools require different actions. A developer account, app registration, a user's consent, and a successful API operation are separate facts.

| Tool or source | Presenter setup | Proof to collect |
| --- | --- | --- |
| Local files and document tools | Select supported sample files and templates. | File metadata, extracted fields, generated output that opens correctly. |
| Baserow / Frappe | Create a restricted integration identity and API credentials in the owned instance. | Allowed operation succeeds; disallowed operation fails; credentials are redacted. |
| OpenEMR | Enable the relevant API, register the client, and complete the test user's OAuth grant. | Actual consent, granted scopes, token-backed operation, and successful read-back. |
| Football data | Register for the free tier and configure the issued key. | Actual successful response plus documented rate/freshness limits. |
| OpenF1 historical data | Query the public historical endpoint. | Real response, historical event date, retrieval time, and saved source reference. |
| eBay sandbox | Obtain developer-account approval, sandbox keys, and a test user grant. | Separate evidence for approval, authorization, and the resulting sandbox object. |

Use provider-granted status only after it has actually occurred. A locally implemented permission demonstration should be labelled as such. Preserve a redacted setup guide and the real connection check so the presenter can repeat the process.

## Cost accounting

Confirmed user requirement: $0 required subscriptions, API charges, or paid trial credits. Free hosted accounts are allowed. The budget assumes the presenter already owns the computer and has an internet connection.

- Local application, tool, and worker execution uses existing CPU, RAM, disk, and electricity; document those resource requirements when measured.
- Hosted API usage must stay inside the verified free allowance. A connector must fail visibly or defer work when its allowance is exhausted; it must not silently upgrade.
- No paid AI dependency is required. Supported templates, parsing, rules, and local OCR can demonstrate the workflows. Any proposed local model needs a separate machine-capacity check.
- Document source attribution, permitted display/redistribution, account requirements, and current terms when enabling a public-data connector. Pricing and endpoint entitlements must be rechecked during implementation.
- A real business deployment can add hosting, support, delivery, transaction, or licensing costs. The cost view separates those deployment choices from the $0 presentation path.

## Capacity claims and measurement

Capacity explanations are engineering designs until tested. Record machine specification, fixture size, concurrent users, throughput, peak memory, latency distribution, failure/retry count, and API usage for actual measurements.

The implemented sports connector makes three requests per historical refresh. A five-minute schedule running all day produces `3 x 288 = 864` provider requests before retries. This is arithmetic, not a provider quota or throughput benchmark. Unchanged mapped input reuses the previous run. A production adapter should enforce the provider's burst allowance and share cached facts across subscribers; the present demo has one configured source timer and one report recipient. The separately verified one-minute Google timer saved 30 rows into each event workplace and was then disabled.

Load tests run against owned local applications or controlled fixtures. Provider sandboxes and free public APIs are exercised only at permitted normal usage rates.

## Remaining evidence before implementation claims

Select the actual real-tool integrations, verify their versions and install footprints, complete necessary free registrations, inspect supported write routes and required fields, and run connection checks. Documentation research alone is not an integration test. Capture and report actual results as those steps are completed.
