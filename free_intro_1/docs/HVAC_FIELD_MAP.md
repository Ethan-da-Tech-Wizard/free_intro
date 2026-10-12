# HVAC: concrete repeated-field example

These synthetic values and schemas are implemented in the running demo. Actual manual and automatic records are documented by the screenshot manifest.

## The eight facts entered three times

| Fact | Sample value | Customer Profiles | Dispatch Desk | Billing Desk |
| --- | --- | --- | --- | --- |
| Customer reference | `C-014` | `customer_ref` | `external_customer_ref` | `account_ref` |
| Full name | `Avery Example` | `display_name` | `contact_name` | `addressee` |
| Phone | `+1 480 555 0146` | `phone` | `contact_phone` | `recipient_phone` |
| Email | `avery@example.invalid` | `email` | `contact_email` | `delivery_email` |
| Street | `100 Sample Lane` | `street` | `site_address` | `billing_address` |
| City | `Mesa` | `city` | `city` | `city` |
| Region | `AZ` | `region` | `region` | `region` |
| Postal code | `85201` | `postal_code` | `postal_code` | `postal_code` |

The manual demonstration saves all eight facts separately in each app. The automated demonstration saves them once and maps them into the other two apps. Keep the postal code as text. Preserve both the entered phone value and the normalized comparison form where useful.

## Work that is specific to the job

The request says the AC is blowing warm air. The fixture identifies an outdoor unit, access instructions, a requested visit window, and a diagnostic fee from a seeded rate sheet. Those are distinct facts: the operator selects the actual available visit slot, and the rate sheet supplies the draft charge. Reusing an address does not eliminate the need to make those decisions.

The service and billing address match in this demonstration's shared schema. Distinct addresses require an extended contract. Existing customers match by explicit customer reference; a new job reference and slot create another visit while retaining the customer's saved ID. Run history preserves the values verified for each execution.

## Implemented sequence

1. Enter the single intake, or import the PDF/workbook and review the mapped fields.
2. Save to Customer Profiles through its HTTP API; retain the returned record ID.
3. Reserve the selected slot and write the dispatch job with the customer record in `_linked_records`.
4. Retain the dispatch ID; create a billing draft referencing both upstream records.
5. Store all target identifiers with the workflow run and read the records back.
6. When a technician completion event arrives, update the existing billing draft with the approved time and parts. Do not create a second draft for the same job.

## Exercised cases

- Clean intake with matching service and billing addresses.
- Existing customer with an additional service visit and retained customer ID.
- Missing postal code or unreadable scanned field.
- Technician slot taken before the reservation is saved.
- Billing unavailable after dispatch succeeds.
- Repeated intake and repeated technician completion events.

The capture gallery covers the same source through manual and automatic paths, actual denied API access, restored access, resumed billing, and a completion event updating the invoice. The eight shared facts produce a structural comparison of 24 manual entries versus 8 once. Across all fields the manual forms have 32 entries versus 15 intake fields. No measured human timing is claimed.
