# Automation studio: team charter and demo brief

Status: implemented as Relayworks. Eight workflows, 24 local workplace apps, actual before/after screenshots, live public Google Sheets and historical OpenF1 reads, document tools, and automated runs are available with $0 required service charges. No private external accounts or commercial business vendors have been connected. See the presenter guide and implementation record for delivered behavior.

## Mission

You already have the tools. We make them work together.

Build a complete showcase of how accessible information can become useful automated work: read a file or service, interpret and validate its data, reuse known information, and deliver a verified result in the tools people already use. The presenter must pay no required subscription, API charge, or trial fee. Local tools and usable free hosted accounts are allowed; document limits and resource needs.

These are specialist roles for the assistant's working persona. The sector lenses define the expertise each role should apply; they are not claims about actual employees or personal employment histories.

## Confirmed audience and presentation

Serve both business viewers and technical evaluators through the same working demonstration.

- The default view explains the task in plain language, shows the input, supports any required review, and lets the viewer inspect the completed paperwork and updated records.
- An optional technical view exposes the actual run's data mappings, source references, API activity, granted permissions, validation, and retry or failure history. Credentials and sensitive payload values remain protected.
- Both views describe the same underlying execution and verified results. Technical detail is available on demand without being required to finish the business task.

The product and frontend roles own the two presentations. Integration and automation roles provide real execution evidence, the access role reviews what can be displayed, and quality verifies that both views agree.

## Roles and accountability

| Role | Sector lens | Duties throughout the SDLC | Evidence of completion |
| --- | --- | --- | --- |
| Product and workflow lead | Small business operations and administrative services | Identify the audience, map current manual work, select the demonstration, define supported cases and acceptance criteria, own scope and final acceptance. | A concrete before-and-after workflow and an agreed completion checklist. |
| Technical lead and architect | Enterprise systems and legacy modernization | Check feasibility, define shared data structures and connector boundaries, choose the implementation, review changes, resolve cross-system failures. | A coherent design whose full workflow runs successfully. |
| Integration engineer | SaaS platforms and business systems | Research official interfaces, connect APIs and webhooks, support file imports/exports, implement authorization, pagination, quotas, and connection checks. | Each selected connector reads or writes its real target and verifies the result. |
| Data and document engineer | Records processing, logistics, and office workflows | Handle supported PDFs and spreadsheets, OCR when required, map fields, retain source references, validate values, reuse saved profiles, and produce completed documents. | Correct extracted values and usable output files for the agreed examples; uncertain values can be reviewed. |
| Automation and backend engineer | Transaction processing and scheduled operations | Implement triggers, workflow state, persistence, retries, duplicate prevention, scheduling where needed, and recovery from partial completion. | Repeating or resuming an operation produces the intended result without duplicate effects. |
| Product designer and frontend engineer | Business software and accessible interfaces | Build connection setup, uploads, field mapping, previews, corrections, progress, useful errors, and a clear demonstration of results. | A viewer can complete the chosen task and understand what changed. |
| Access and security engineer | Enterprise identity and account administration | Determine required access, distinguish app registration from user consent, protect credentials, implement revocation handling, and control access to stored documents. | Granted permissions match the task, secrets stay private, and loss of access is handled correctly. |
| Quality and release engineer | Service reliability and deployment | Verify the end-to-end workflow and meaningful failures, prepare repeatable setup and reset, check persistence and restart behavior, document operation and troubleshooting. | A fresh setup can reproduce the demo; the acceptance checklist has recorded results. |

The technical lead coordinates these responsibilities. Roles are ownership and review lenses; they do not require separate agents or people for every task.

## SDLC responsibilities

1. Discovery: the workflow lead captures the audience, real repetitive task, sample inputs, desired outputs, and success criteria. Integration and document specialists check feasibility immediately.
2. Design: the architect defines data flow and failure behavior; design and access specialists define setup, review, permissions, and credential handling.
3. Implementation: integration, document, automation, and interface work follows the same agreed workflow. Test meaningful behavior as it becomes runnable.
4. Verification: quality checks the complete workflow, output correctness, duplicate handling, uncertain input, interrupted work, and authorization failures that apply to the selected tools.
5. Delivery: release engineering proves setup, restart, reset, and operation. Product accepts the agreed demonstration against evidence.
6. Operation and handoff: document how to reconnect services, change mappings, inspect failures, and rerun work safely.

These are activities required to finish one demonstration, not separate product versions.

## Confirmed showcase direction

Create realistic manual workflows with multiple moving parts, then connect them with actual APIs and tools. Use fictional people, companies, and varied reports. Every selected story includes usable manual applications, screenshots of repeated field entry, an automated execution from the same input, verified saved results, and a structural flowchart.

The HVAC centerpiece has separate customer-profile, dispatch, and billing applications. Enter shared information once and populate the other systems through their APIs. Sports reporting must explain whose preferences are local, where public data comes from, how it is fetched, and the cost and capacity limits. Research additional complete stories for law offices, clinics, stores, individual sellers, and other everyday workplaces.

The elaborated proposal includes eight stories and their before/after steps. See [showcase blueprint](docs/SHOWCASE_BLUEPRINT.md), [workflow catalog](docs/WORKFLOW_CATALOG.md), [source and cost research](docs/RESEARCH.md), and [screenshot/evidence plan](docs/EVIDENCE_PLAN.md). Editable flowcharts are in [the Archi project](diagrams/showcase.archi.json).

## Integration approach

Use an official API when available. Support files, database access, command-line interfaces, and import/export formats where they fit the source. Consider browser automation for a selected service only after inspecting its actual interface, access requirements, and operating constraints.

Each selected integration has a record of:

- The actual service and account or local application involved.
- Supported reads, writes, input types, and outputs.
- Required authorization and who can grant it.
- Whether developer registration or provider review is needed.
- Software cost, hosting needs, free usage limits, and any paid dependency.
- Connection state and evidence from the most recent test.
- Error behavior, retry behavior, and recovery instructions.

Show access accurately: not configured, awaiting authorization, connected and tested, or needs attention. A provider's app approval, an account owner's consent, possession of a token, and a successful API call are distinct events. Display granted access and successful results without displaying secret values.

The user may need to create accounts, register an application, grant access, or submit a provider's application form. Requirements depend on the selected service. Research and prepare those steps concretely; do not invent approvals or assume every provider uses an API key.

## Real candidate tools

Official documentation checked on 2026-09-23. These are researched candidates, not installed or verified integrations.

| Candidate | Possible demonstration role | Access and cost information |
| --- | --- | --- |
| LibreOffice | Work with Excel-format spreadsheets and generate office documents or PDF output. | Free, open-source desktop software. The demo's generated XLSX was opened and converted in an actual LibreOffice check. [Official overview](https://www.libreoffice.org/) |
| Paperless-ngx | Ingest and OCR documents, retain originals, and retrieve searchable content through an API. | Open-source document management software with a REST API and token authentication. A running instance requires a host. [Project documentation](https://docs.paperless-ngx.com/), [REST API](https://docs.paperless-ngx.com/api/) |
| Baserow | Display real customer or job records that the workflow creates and updates. | REST API with database tokens controlling table operations; free cloud and self-hosted plans exist, with different limits and paid features. [Database API](https://baserow.io/user-docs/database-api), [Plans](https://baserow.io/user-docs/pricing-plans) |
| Google Sheets | Demonstrate a familiar hosted spreadsheet updated after user authorization. | Standard API use currently has no additional charge within quotas. Current documentation announces charges for exceeding quota limits later in 2026, so pricing must be rechecked at implementation. OAuth permissions and app verification depend on scope. [Usage and pricing](https://developers.google.com/workspace/sheets/api/limits), [Authorization scopes](https://developers.google.com/workspace/sheets/api/scopes) |

Free software does not itself supply free hosting. The selected deployment must meet the user's cost requirement. Local Excel-format file processing and access to a hosted Microsoft account are separate integration choices.

## Definition of a complete working demo

- Every agreed story runs from initial setup and input through verified output in its selected tools.
- Manual workplace applications are usable, and actual screenshots document the before/after comparison for the same input.
- Each story has an editable flowchart and a source/access/cost/capacity explanation consistent with its implementation.
- Supported document types, templates, and field mappings are explicit and exercised with representative inputs.
- Every visible action required by the workflow works; displayed connection states reflect real results.
- A business viewer can complete the workflow through the simple view, and a technical evaluator can inspect evidence from that same run in the optional technical view.
- Repeated profile information is persisted and reused correctly.
- A user can inspect and correct missing, conflicting, or uncertain values before dependent actions proceed.
- Generated files open correctly, and external writes can be inspected in the target application.
- Duplicate inputs, interrupted runs, and service failures have tested behavior appropriate to the chosen workflow.
- Credentials are protected and access can be revoked or reconnected.
- Setup instructions, sample data, reset instructions, and a demonstration script allow another person to reproduce the result.
- The acceptance record distinguishes passed checks, known limitations, and anything still blocked. A required integration awaiting credentials is unfinished.

## Discovery decisions

1. Audience — confirmed: both business and technical viewers, with a simple demo and an optional technical view. Intended use as a sales demonstration, portfolio, or reusable product remains open.
2. Showcase — confirmed: multiple detailed manual-to-automated stories, including HVAC dispatch/profile/billing, sports reports, law offices, clinics, shops, and individual sellers. The proposal adds property repairs and community events.
3. Actual tools: must-have applications and services, available accounts, and any software the user already pays for.
4. Meaning of free — confirmed: no required service charges to present the showcase; local tools and free hosted accounts are permitted, with costs and limits documented.
5. Delivery: a browser app on this computer, a self-hosted shared service, a public demo, or a desktop application; who needs access and on which operating systems.
6. Inputs — confirmed direction: fictional people and businesses with varied synthetic reports and forms. External sports facts should use actual permitted provider data, clearly labelled by freshness and source type.
7. Automation control: which outputs should be reviewed and which actions should run automatically; whether paperwork is only prepared or also submitted.
8. Completion criteria: the exact outcomes a viewer must be able to inspect, repeat, and verify before the demo counts as done.

The delivered choices are a local browser app, a historical F1 example, eight workplace stories, generated messy files, public Google sample data, and explicit human review for uncertain inputs. The presenter guide and implementation record supersede earlier open-ended packaging and integration suggestions.
