"""Align explanatory scenario notes with the implemented runtime contracts."""
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from config import DEFINITIONS

source=ROOT/'docs/scenarios.json'
catalog=json.loads(source.read_text())
catalog['status']='Implemented local workflows with real public sources and actual browser evidence'
followups={
 'hvac':'Apply a uniquely referenced completion event. Update the existing billing draft with diagnostic fee, approved labor, and parts. Reuse the customer for later jobs.',
 'sports':'Optionally fetch OpenF1 historical driver/session/lap data. Review the provider date, compute the best positive lap duration, and export a calendar file or local briefing.',
 'legal':'A seeded possible party match holds the intake until the reviewer records a decision. Generate a populated administrative client packet and dated task.',
 'clinic':'Reserve the selected provider and time atomically. A competing patient cannot receive the occupied slot; correct the input and rerun.',
 'retail':'Receipt identity prevents duplicate stock increments. Derive available quantity from stock minus reserved units and save that value to the storefront.',
 'reseller':'A unique sale event decrements the one-off item to zero, marks the local listing sold, and fills the packing slip. A second distinct sale fails.',
 'property':'Match a contractor invoice to its ticket and approved estimate. Mismatched references or an unapproved overage stop before the follow-up writes.',
 'events':'Allocate the session seat or mark the attendee waitlisted. Only an attendee with a reserved seat can be checked in.'}
rules={
 'hvac':['A technician/time combination can be reserved by one job.','Customer reference is the explicit matching key; no fuzzy identity decision is implied.','Invoices stay drafts. Unique completion events apply approved labor and parts; payment is not charged.'],
 'sports':['Provider event date and retrieval time are distinct.','OpenF1 historical reads need no key; paid live access is excluded.','Recipient details are synthetic; provider facts retain provenance.'],
 'legal':['Existing demo client is the seeded possible-party-match trigger.','Reviewer confirmation is required; it does not bypass missing fields or invalid dates.','Documents and tasks are administrative demo outputs; no legal filing occurs.'],
 'clinic':['All patient information is synthetic.','Provider/slot allocation is transactional and rejects double booking.','The generated packet is administrative; no clinical decisions are made.'],
 'retail':['The demonstration SKU catalog is FLT-20, KIT-07, and BOLT-12.','A repeated receipt cannot increment stock again; changed receipt quantities need a new reference.','Reserved stock cannot exceed on-hand stock.'],
 'reseller':['Each unique item starts with one unit.','A sale needs a unique event reference and an available unit.','Listings and packing paperwork are local drafts; no marketplace or carrier is contacted.'],
 'property':['Invoice job reference must match the repair ticket.','An amount above the approved estimate is held for review.','A matched invoice updates local records without making a payment.'],
 'events':['Registration reference is the stable business key when supplied.','Capacity allocation is transactional; full sessions become waitlisted.','Check-in requires an existing reserved seat.']}

for story in catalog['scenarios']:
    s=DEFINITIONS[story['id']];key=s['id']
    story['sources']=['Generated labelled intake PDF and editable sample facts','Generated messy XLSX/CSV with original rows, normalization, duplicate flags, and review']
    if key=='sports':story['sources'].append('Actual OpenF1 historical session 9158 / driver 1, with a timestamped offline recording')
    if key=='events':story['sources'].append("Actual Google developer sample Sheet export; names/majors map to attendees/sessions, other facts are labelled defaults")
    common=set.intersection(*(set(fields) for fields in s['stage_fields']))
    story['shared_fields']=[f['label'] for f in s['fields'] if f['key'] in common]
    story['manual']=[f"Open {t['name']}, enter its {len(s['stage_fields'][i])} source fields, and save to its independent store." for i,t in enumerate(s['targets'])]
    story['manual'].append('Compare the three saved records and download each populated document. Reconcile mistakes by returning to the source facts.')
    story['automated']=['Enter or import the source once; inspect original and normalized values, map fields, and correct review flags.',
       'Validate the shared intake and persist a job with source provenance and business identity.',
       'POST each mapped record to its own local workplace HTTP API, retaining the returned IDs for later steps.',
       'GET each saved record and compare its payload. Keep successful steps when a later destination fails.',followups[key]]
    story['demo_routes']=[f"POST /v1/{t['id']}/records" for t in s['targets']]
    story['mapping_examples']=[f"{f['label']} -> "+' -> '.join(t['id']+'.'+t['mapping'][f['key']] for t in s['targets']) for f in s['fields'] if f['key'] in common][:3]
    story['mapping_examples'].append('Run ID + stage -> idempotent operation ID; verified upstream record IDs -> downstream _linked_records metadata.')
    story['rules']=rules[key]
    story['failure']='Revoke access or take the third destination offline. The API returns 403/503; restore it and resume the saved job without rewriting completed stages. '+followups[key]
    story['cost']='The three local apps and standard-library processing require $0 service fees. Poppler/Tesseract are free local tools. Business vendors listed in the research are documented candidates, not connected services.'
    if key=='sports':story['cost']+=' OpenF1 historical access is free; the paid live service is excluded.'
    if key=='sports':story['scale']='Each historical refresh makes three GET requests. A five-minute timer running for a full day makes 3 x 288 = 864 provider requests before retries; this is arithmetic, not a provider quota or a throughput benchmark. Unchanged mapped input reuses the saved run. Production fan-out would need shared caching, provider-aware rate limits, and bounded queues.'
    if key=='events':story['cost']+=' The public Google CSV export requires no account or key; availability is controlled by Google.'
    story['evidence']=['Actual browser captures show source paperwork, all three manually typed/saved forms, one intake, three automated records, HTTP proof, and failure/recovery.','The capture manifest records timestamps, URLs, modes, record IDs, source type, and file hashes.','Processing milliseconds are measured per run. Field-entry counts are structural comparisons, not human timing claims.']
source.write_text(json.dumps(catalog,indent=2,ensure_ascii=False)+'\n')
print('Synchronized eight workflow descriptions with the running contracts.')
