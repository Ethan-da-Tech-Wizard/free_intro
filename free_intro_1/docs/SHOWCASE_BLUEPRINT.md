# Automation showcase: realistic work, visible proof

Status: delivered as the local Relayworks application. Eight workflows, 24 independently saved workplace apps, real public sources, document tools, and actual screenshot evidence are implemented. [IMPLEMENTATION.md](IMPLEMENTATION.md) defines the tested runtime and supported boundaries; [PRESENTER_GUIDE.md](PRESENTER_GUIDE.md) explains presentation.

## Confirmed direction

- One complete showcase contains multiple detailed workplace stories.
- Business viewers get a simple presentation; technical viewers can inspect the same run.
- Each story includes clickable workplace applications, actual screenshots of manual entry, a working automated path, and inspectable results.
- Fictional people, companies, and reports provide repeatable examples. Real software tools and API connections do the work.
- The presenter can run the showcase without required subscriptions, paid API usage, paid AI, or expiring trial credits. Local tools and free hosted accounts are permitted.
- Every story explains the source, movement, mapping, destination, access requirements, cost, and scaling behavior of its information.
- Archi supplies editable diagrams. Located at `/home/ethan/pg/archi`; planning outputs stay inside this project.

## The presentation

The visitor selects a workplace and sees the person, the task, and the source documents. The presenter can then follow the same sequence for any story:

1. Open the source report or request and the three workplace applications.
2. Perform the manual work. Repeated fields are visible, and saved records belong to their respective applications.
3. Inspect the resulting records and any deliberately seeded inconsistency.
4. Reset to the same starting dataset, preserving the manual evidence.
5. Enter or import the information once, review uncertain values, and run the connected workflow.
6. Open the real destination records and generated documents.
7. Compare the captured screens and observed work counts.
8. Optionally inspect mappings, API activity, permissions, costs, and the flowchart.
9. Trigger the story's failure example, recover, and show that the final records remain correct.

The same input and required output are used in both paths. Setup time, ongoing operation, and exception review are described separately. Elapsed-time claims come from actual timed runs; designed field counts are labelled as such.

The manual story must reflect plausible work across disconnected tools. Retain useful native autofill, import, and template features in any real software shown. For example, ERPNext already carries data between certain upstream documents and invoices; our added value must be demonstrated at the remaining system boundaries and in the review, reliability, and reporting behavior.

## The HVAC centerpiece

The fictional Desert Air company has three independently saved applications:

| Application | What the visitor does manually | What the automation does |
| --- | --- | --- |
| Customer Profiles | Enter name, contact details, address, customer reference, preferences, and access notes. | Match or create the customer, store the profile, and retain its identifier. |
| Dispatch Desk | Retype customer/site information, enter the issue and equipment, choose a technician and slot. | Map the saved information, check availability, reserve the selected slot, and create the job. |
| Billing Desk | Retype the billing details, connect the job, enter the fee, then copy approved time and parts after completion. | Create the linked draft, update it from a unique completion event, and generate the invoice preview. |

Eight shared fields appear in each of the three manual forms. The designed comparison is 24 shared-field entries manually versus 8 entered once, eliminating 16 repeated entries. Unique job decisions, review, and missing information still require their appropriate inputs. This is a specified example, not a measured productivity result.

The operator begins in the single intake or maps a supported PDF/spreadsheet into it. The workflow saves Customer Profiles first and carries its ID into downstream record metadata. Manual workplace forms save only to their own app. The [HVAC field map](HVAC_FIELD_MAP.md) gives implemented values and destination names.

The strongest recovery scene: billing is unavailable after customer and dispatch saves succeed. The run shows precisely what completed. Restore billing and resume; it creates the missing draft once and reads back all three records. A new customer or job must not appear as a side effect of that retry.

The technician's completion is a separate event. Scheduling a job does not claim that work is complete or that payment has occurred. A billing draft is labelled as a draft.

## Eight implemented workplace stories

| Story | Repeated work | Visible result |
| --- | --- | --- |
| HVAC dispatch | Copy customer and job details into three systems. | Customer history, dispatched job, billing draft. |
| Sports reporting | Check sources, retype results, update schedules, compose a digest. | Sourced worksheet, schedule, and report that refresh together. |
| Law office | Repeat intake details in a matter file, documents, and task calendar. | Reviewed matter, assembled packet, linked tasks. |
| Clinic | Repeat synthetic registration data in scheduling and intake documents. | Matched patient, appointment, administrative packet. |
| Retail shop | Re-enter counted stock from supplier paperwork into inventory and storefront. | Reconciled receipt, stock movements, online quantities. |
| Individual seller | Repeat an item's description, dimensions, and sale details. | Draft listing, correct stock state, packing paperwork. |
| Property manager | Copy a repair request through contractor work and owner reporting. | Linked ticket, work order, matched invoice/report. |
| Community organizer | Copy registrations into rosters, sessions, and badges. | Capacity-controlled schedule, badges, attendance report. |

[The detailed catalog](WORKFLOW_CATALOG.md) expands every story with actors, inputs, manual steps, automated steps, mappings, rules, failures, evidence, and capacity considerations. Its editable source is [scenarios.json](scenarios.json).

## Sports: where the information really comes from

Alex's preferences are a synthetic, locally saved personal profile. Team results and fixtures come from the selected external provider. The workflow joins them by provider IDs; it does not retrieve private information about an arbitrary person.

For a football demonstration, candidate requests are `GET /v4/competitions/{code}/matches` and `GET /v4/competitions/{code}/standings` on football-data.org, subject to the free account's actual entitlements. The token lives in the backend. Responses include provider record IDs and timestamps; our fetch additionally records retrieval time. The free plan has delayed information, which remains labelled delayed.

For an athlete-specific example without an account, OpenF1 historical sessions can provide driver and lap data. Historical data is explicitly labelled historical; the paid live service is not needed. NBA is another candidate, but the reviewed BALLDONTLIE free tier does not include individual game statistics. These differences determine which story we can honestly demonstrate for free. See [research and sources](RESEARCH.md).

The scheduler should fetch once for a group of reports, cache by provider/resource/query, normalize records, and generate each person's report from that cache. A moved fixture updates its existing schedule entry. An API timeout preserves the last good data and displays its age. A saved response used for an offline presentation is labelled a recording and cannot serve as proof of a current provider connection.

## Software structure

| Component | Responsibility |
| --- | --- |
| Presenter workspace | Choose a story, load/reset a seed, compare manual and automatic runs, and open evidence. |
| Workplace applications | Separate screens, schemas, validation, saved records, and HTTP interfaces for the domain systems. |
| Intake tools | Read supported forms, CSV/XLSX files, text PDFs, and agreed scanned-PDF examples. |
| Workflow service | Persist steps and output IDs, validate input, apply mappings, queue work, and resume partial runs. |
| Connector adapters | Call actual demo-app APIs and selected real tools; translate schemas, authentication, and errors. |
| Profile store | Reuse confirmed customer, company, seller, or organizer details without overwriting stronger source information silently. |
| Evidence store | Associate source references, redacted request/response summaries, read-back results, files, screenshots, and measurements with the run ID. |
| Local message destination | Display generated confirmations and digests in an owned test inbox. |

The automation must cross real API or tool boundaries. Having three panels read one shared browser object would not meet the independent-system requirement. A reusable interface shell is fine; each workplace application's data ownership and behavior remain explicit.

Local endpoints in the catalog are implemented demo interfaces. Google public exports and OpenF1 historical endpoints are the verified external readers. Other vendor interfaces are researched candidates and are not represented as connected.

## Field mapping and change ownership

Each mapped value records source type, document location or provider record, source revision, target field, transformation, and review status. Examples include a single name becoming a dispatch contact and billing addressee, or a supplier SKU becoming a storefront product ID.

Define an owner for each fact. Customer contact information can belong to the profile, the chosen visit slot to dispatch, and posted invoice amounts to billing. A later address correction should follow an explicit update rule; historical documents must not silently change. Show disagreements instead of guessing which value should win.

Source identifiers, target identifiers, and correlation IDs are distinct. Store their mapping. Use a stable event or operation key to prevent duplicate effects; when a provider lacks native support, query/reconcile the destination before retrying an uncertain write.

## Runtime and cost

Delivered presentation: a browser on the user's existing computer, one Python process with two local HTTP listeners, 24 SQLite workplace stores, and installed Poppler/Tesseract tools. No container installation or paid hosted account is required. Python's standard library supplies the runtime; Playwright is used only for development verification and capture.

Free hosted accounts can add recognisable connections. The normal presentation must expose their real limits and connection state. Internet availability, provider approval, and credentials are setup facts, not assumed successes. A required connector still awaiting credentials remains unfinished.

The cost panel separates software/API fees from the existing computer's resources. It can estimate how work grows, but displayed capacity and elapsed-time claims require measured evidence. All load tests target owned local services. See [research and capacity method](RESEARCH.md).

## Evidence and acceptance

The [evidence plan](EVIDENCE_PLAN.md) defines ten required capture positions per story, the comparison method, and the proof needed for API connections. Screenshots must come from the running tools and be associated with the appropriate run. Diagram exports are explanations, not screenshots of completed workflows.

Every selected story must pass its manual path, automated path, same-input comparison, result inspection, duplicate check, failure/recovery case, reset, and restart check. Every advertised real-tool connection must have an actual test result. The entire collection is one finished deliverable; ordering the work does not reduce those completion requirements.

## Team responsibilities added by this scope

- Workflow lead: research the actual office process, write the actor's script, and define fair manual/automatic comparisons.
- Integration and access roles: document providers, access steps, exact operations, costs, and current free limits.
- Data/document role: create varied synthetic inputs, reusable profiles, templates, mappings, and ambiguous examples.
- Frontend role: build usable manual workplace applications and the optional technical inspector.
- Automation role: make cross-system changes real, persistent, resumable, and verifiable.
- Quality/release role: capture screenshots, retain source/run provenance, measure claims, verify every scene, and package a repeatable presentation.

## Choices still useful while elaborating

Delivered choices: Relayworks visual identity, historical F1 data, a public Google classroom sheet, generated ugly workbooks and labelled PDFs, eight local workplace stories, and short or technical presenter routes. External private-account integrations remain separately documented extensions; none is required to present the working demo.
