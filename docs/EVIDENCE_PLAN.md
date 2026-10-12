# Before/after captures and proof

Status: actual browser evidence captured. `evidence/manifest.json` indexes 134 screenshots with URLs, timestamps, record IDs, modes, and hashes. PNGs under `diagrams/` are explanatory Archi flowcharts; PNGs under `evidence/` are actual running-app captures. `npm run capture` reproduces the evidence using scripted entry, real saves, resets, automated runs, and failure/recovery.

## Per-story capture sequence

Every story has clickable manual applications and an automated workflow. Capture the real interface at these positions, using the same seed and a fixed browser viewport:

| Capture | Required content |
| --- | --- |
| `01-source` | Original report, document, file, or provider record, including source and timestamp. |
| `02-manual-app-a` | First workplace form with the shared fields actually entered and saved. |
| `03-manual-app-b` | Second form with the same facts entered again. |
| `04-manual-app-c` | Third form or report with the relevant facts entered again. |
| `05-automation-review` | Single intake/import, field mapping preview, and any required correction. |
| `06-after-app-a` | Saved result in the first target, with its actual record identifier. |
| `07-after-app-b` | Saved result in the second target, with its actual record identifier. |
| `08-after-app-c` | Saved result in the third target, with its actual record identifier or generated file. |
| `09-technical-trace` | Real run steps, redacted request summaries, read-back evidence, and source/target mappings. |
| `10-failure-recovery` | The story-specific failure and the recovered result; use a paired capture if both cannot fit legibly. |

The eight implemented stories include the ten required capture positions, paired manual-entry/manual-save and failure/recovery views, selected domain exceptions, and actual public-source propagation. Capture filenames identify the story, mode, and step. Scripted typing is evidence of operation, not measured human performance.

Screenshots are produced from actual browser/tool interactions. Do not synthesize UI images or fill fake success logs to stand in for execution. If annotations are useful, retain the unmodified original capture and identify the annotation layer. Any provider sandbox, synthetic record, or recorded response is labelled accordingly.

## Fair comparison

- Reset both paths to the same fixture revision.
- Use the same business requirements and intended outputs.
- Preserve native autofill, imports, templates, and lookups available in the tools being compared. The manual example models disconnected systems; any integration a real product already supplies belongs in the baseline.
- Count deliberate field entry, repeated facts, app switches, corrective actions, and outputs checked.
- Record setup/configuration work separately from recurring task work.
- Label the HVAC 24-to-8 field-entry example as a design count until verified against implemented forms.
- Time actual runs; distinguish human elapsed time, automated processing time, and review time.
- Show output correctness and unresolved exceptions alongside speed.

## Evidence manifest

Each capture and run records `scenario_id`, `fixture_revision`, `run_id`, `mode`, `step_id`, `captured_at`, `app_url`, `target_record_id`, `source_kind`, `viewport`, and the artifact path. A file hash helps associate the displayed evidence with the retained artifact.

Connection evidence additionally identifies the provider, account/environment label, permitted operation, redacted authentication type, test time, response status, and read-back result. Keep actual credentials out of screenshots, exports, and logs.

## Presentation controls

Load a story; open all three apps; follow manual steps; save evidence; reset; run automation; inspect results; show the flowchart; explain costs; trigger the failure; resume; export the evidence bundle. The presenter should be able to repeat this without editing code or losing the previous run's proof.

## Completion checklist for each story

- The operator can complete the manual task using the apps.
- Automatic execution starts from the same source and performs the intended cross-system changes.
- Saved records and generated files agree with reviewed input.
- Duplicate inputs/events do not duplicate effects.
- The documented failure is visible and can be recovered appropriately.
- Reset and restart preserve the intended separation between fixtures and captured runs.
- Screenshots and the technical trace correspond to real executions.
- The diagram, source/cost explanation, and implementation describe the same workflow.
- Any external source is correctly labelled live fetch, provider-delayed, historical, sandbox, synthetic fixture, or recorded response, as applicable.
- Required accounts and tools have been tested, and the presentation incurs no required service charge.
