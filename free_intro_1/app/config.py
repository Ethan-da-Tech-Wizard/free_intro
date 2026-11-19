# ==============================================================================
# Program: config.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Educational automation and workflow orchestration module for free_intro.
#          Provides structured data generation, asset planning, and contracts.
# ==============================================================================
"""Scenario contracts for the running local showcase."""

# How this file fits the app: the single source of truth for what the eight demo "workplaces" look like.
# app/engine.py imports DEFINITIONS to validate input and to know the three destination apps of each
# scenario; app/server.py exposes public_config() as GET /api/config so web/app.js can draw the forms and
# mapping screens without duplicating any field list; tests import it to build sample data.
# Nothing here touches the network or a database: it reads docs/scenarios.json once at import time (story
# text, actors, rules, app names, outputs per scenario) and merges it with the field contracts defined
# below. A scenario id missing from that JSON raises KeyError at start-up, which is the intended fail-fast
# behaviour.
# Adding a scenario: add its entry to docs/scenarios.json AND to DEFINITIONS (same id), give it three
# entries in stage_fields/keys, and, if it needs a follow-up action, a matching branch in
# Workplaces.save() in engine.py.
# Known limits: the data is demonstration-only (example.invalid emails, +1 555 phone numbers);
# stage_fields lists below are long literal rows because they are data tables, not logic.
import json
from pathlib import Path

# Repo root (parent of app/); used to find docs/scenarios.json and, in other modules, web/ and fixtures/.
ROOT = Path(__file__).resolve().parents[1]
# Narrative/catalog data per scenario (story, actor, rules, app names, outputs) loaded once at import time.
# Keyed by scenario id so DEFINITIONS can be enriched with it below.
CATALOG = {s['id']: s for s in json.loads((ROOT / 'docs/scenarios.json').read_text())['scenarios']}


def field(key, label, value, kind='text', required=True):
    """Build one form-field descriptor.

    Args:
        key: machine name used in payloads.
        label: human label shown in the UI and in validation messages.
        value: default/sample value (also supplies fixture data).
        kind: "text", "email" or "number"; drives validation in engine.validate.
        required: whether an empty value is rejected.
    """
    return {'key': key, 'label': label, 'default': value, 'type': kind, 'required': required}


# Contact fields shared by every scenario. Each scenario prepends this block to its own fields so that
# "customer" data looks the same across the three apps in a workflow.
CUSTOMER = [
    field('customer_ref', 'Customer reference', 'C-014'),
    field('full_name', 'Full name', 'Avery Example'),
    field('phone', 'Phone', '+1 555 555 0146'),
    field('email', 'Email', 'avery@example.invalid', 'email'),
    field('street', 'Street', '100 Sample Lane'),
    field('city', 'City', 'Anytown'), field('region', 'Region', 'ST'),
    field('postal_code', 'Postal code', '12345'),
]

# The scenario contracts. One entry per demo business (hvac, sports, legal, ...). Per scenario:
#   short/icon/company/tagline/color : display metadata for the UI
#   primary       : field key that identifies the record in the first app
#   fields        : the intake form (see field())
#   stage_fields  : which fields each of the three destination apps receives
#   keys          : the field used as the external key in each destination (stage 0, 1, 2)
#   action*       : the optional follow-up step (kind, button label, extra inputs)
# The loop at the bottom of this module adds catalog data and the derived "targets" list.

# Reading the rows below: `fields` is the intake form in display order; `stage_fields[i]` lists which of
# those canonical fields the i-th app (0 = first desk, 1 = second, 2 = third) receives; `keys[i]` is the
# field that identifies a record in that app (its external key, so a repeated submission updates instead
# of duplicating).
DEFINITIONS = {
    'hvac': dict(short='HVAC & field service', icon='wind', company='Desert Air',
        tagline='One service request. Three desks, already in sync.', color='#137e72',
        primary='job_ref', fields=CUSTOMER + [
            field('job_ref', 'Job reference', 'JOB-1042'),
            field('issue', 'Reported issue', 'AC is blowing warm air'),
            field('equipment', 'Equipment', 'Outdoor condenser · Unit A'),
            field('technician', 'Technician', 'Morgan Lee'),
            field('slot', 'Visit slot', '2026-10-06 10:00'),
            field('fee', 'Diagnostic fee (USD)', 95, 'number'),
            field('access_notes', 'Access notes', 'Side gate; call on arrival', required=False)],
        stage_fields=[['customer_ref','full_name','phone','email','street','city','region','postal_code','access_notes'],
                      ['customer_ref','full_name','phone','email','street','city','region','postal_code','job_ref','issue','equipment','technician','slot'],
                      ['customer_ref','full_name','phone','email','street','city','region','postal_code','job_ref','fee']],
        keys=['customer_ref','job_ref','job_ref'], action='completion', action_label='Complete the visit',
        action_fields=[field('hours','Approved labor hours',1.5,'number'),field('hourly_rate','Hourly rate (USD)',80,'number'),field('parts','Parts total (USD)',35,'number')]),
    'sports': dict(short='Sports & personal reports', icon='activity', company='Touchline Daily',
        tagline='Follow the data from a public API to your personal briefing.', color='#8057d5',
        primary='event_ref', fields=[
            field('event_ref','Event reference','DEMO-RACE-01'),field('full_name','Report recipient','Alex Example'),
            field('email','Delivery address','alex@example.invalid','email'),field('team','Team / driver','Synthetic Racing'),
            field('event_name','Event / session','Demo Grand Prix'),field('event_date','Event date','2026-10-04 14:00'),
            field('result','Result / best lap','Awaiting source'),field('laps','Laps counted',0,'number'),
            field('timezone','Display timezone','Etc/GMT+7')],
        stage_fields=[['event_ref','team','event_name','event_date','result','laps'],['event_ref','team','event_name','event_date','timezone'],['event_ref','full_name','email','team','event_name','event_date','result','laps']],
        keys=['event_ref','event_ref','event_ref'], action='refresh', action_label='Fetch historical F1 data',action_fields=[]),
    'legal': dict(short='Law office', icon='scale', company='Juniper Legal',
        tagline='An intake packet becomes a matter, documents, and dated tasks.', color='#5662ae',
        primary='matter_ref', fields=[
            field('matter_ref','Matter reference','MAT-0204'),field('full_name','Client name','Casey Example'),
            field('email','Client email','casey@example.invalid','email'),field('phone','Phone','+1 555 555 0114'),
            field('street','Mailing address','42 Sample Avenue'),field('other_party','Other party','Orchard Demo LLC'),
            field('matter_type','Matter description','Business agreement review'),field('appointment','Appointment','2026-10-07 09:00'),
            field('office_name','Office name','Juniper Legal')],
        stage_fields=[['matter_ref','full_name','email','phone','street','other_party','matter_type'],['matter_ref','full_name','email','street','matter_type','office_name'],['matter_ref','full_name','email','appointment','matter_type']],
        keys=['matter_ref','matter_ref','matter_ref'],action='review',action_label='Demonstrate a review hold',action_fields=[]),
    'clinic': dict(short='Clinic administration',icon='heart',company='Cedar Clinic',
        tagline='Synthetic patient details move cleanly into the appointment and packet.',color='#367aa8',
        primary='patient_ref',fields=[
            field('patient_ref','Patient reference','PAT-0310'),field('full_name','Patient name','Jordan Example'),
            field('birth_date','Date of birth','1990-04-12'),field('phone','Phone','+1 555 555 0180'),
            field('email','Email','jordan@example.invalid','email'),field('street','Address','18 Sample Road'),
            field('referral_ref','Referral reference','REF-022'),field('provider','Provider','Demo Provider A'),
            field('slot','Appointment slot','2026-10-08 11:00'),field('visit_type','Visit type','Administrative intake')],
        stage_fields=[['patient_ref','full_name','birth_date','phone','email','street'],['patient_ref','full_name','birth_date','phone','provider','slot','visit_type'],['patient_ref','full_name','birth_date','phone','street','referral_ref','visit_type']],
        keys=['patient_ref','patient_ref','patient_ref'],action='conflict',action_label='Try a conflicting appointment',action_fields=[]),
    'retail': dict(short='Retail & inventory',icon='store',company='Corner Supply',
        tagline='One counted delivery updates receiving, stock, and online availability.',color='#b47b23',
        primary='receipt_ref',fields=[
            field('receipt_ref','Receipt reference','REC-088'),field('supplier','Supplier','Example Wholesale'),
            field('po_ref','Purchase order','PO-031'),field('sku','Internal SKU','FLT-20'),
            field('item_name','Item name','20-inch replacement filter'),field('quantity','Counted quantity',12,'number'),
            field('unit_cost','Unit cost (USD)',8.5,'number'),field('location','Location','Main stockroom'),
            field('reserved','Reserved units',2,'number')],
        stage_fields=[['receipt_ref','supplier','po_ref','sku','item_name','quantity','unit_cost'],['receipt_ref','sku','item_name','quantity','location','reserved'],['receipt_ref','sku','item_name','quantity','reserved']],
        keys=['receipt_ref','sku','sku'],action='duplicate',action_label='Replay the delivery',action_fields=[]),
    'reseller': dict(short='Independent seller',icon='tag',company='Second Story',
        tagline='Describe an item once. Prepare its listing and sale paperwork.',color='#b25c87',
        primary='sku',fields=[
            field('sku','Item SKU','USED-072'),field('title','Listing title','Vintage oak side table'),
            field('description','Description','Solid oak; small mark on rear leg'),field('condition','Condition','Used — good'),
            field('price','Price (USD)',65,'number'),field('weight','Weight (kg)',7.2,'number'),
            field('dimensions','Dimensions','45 x 40 x 52 cm'),field('seller','Seller','Casey Example'),
            field('return_address','Return address','55 Sample Street')],
        stage_fields=[['sku','title','description','condition','price','weight','dimensions'],['sku','title','description','condition','price','weight','dimensions'],['sku','title','price','weight','dimensions','seller','return_address']],
        keys=['sku','sku','sku'],action='sale',action_label='Record a sale',
        action_fields=[field('buyer','Buyer','Taylor Example'),field('ship_to','Delivery address','10 Example Terrace'),field('sale_ref','Sale reference','SALE-019')]),
    'property': dict(short='Property operations',icon='building',company='Maple Properties',
        tagline='Follow a repair from the tenant request to the owner report.',color='#747c34',
        primary='ticket_ref',fields=[
            field('ticket_ref','Ticket reference','FIX-016'),field('property_ref','Property reference','PROP-03'),
            field('unit','Unit','2B'),field('full_name','Tenant contact','Morgan Example'),field('phone','Phone','+1 555 555 0133'),
            field('issue','Reported issue','Kitchen faucet leak'),field('access_window','Access window','2026-10-07 13:00–16:00'),
            field('contractor','Contractor','Demo Plumbing'),field('estimate','Approved estimate (USD)',180,'number')],
        stage_fields=[['ticket_ref','property_ref','unit','full_name','phone','issue'],['ticket_ref','property_ref','unit','full_name','phone','issue','access_window','contractor'],['ticket_ref','property_ref','unit','issue','contractor','estimate']],
        keys=['ticket_ref','ticket_ref','ticket_ref'],action='invoice',action_label='Match a contractor invoice',
        action_fields=[field('invoice_ref','Invoice reference','INV-080'),field('job_reference','Invoice job reference','FIX-016'),field('invoice_total','Invoice total (USD)',180,'number')]),
    'events': dict(short='Community & events',icon='users',company='Gather Workshop',
        tagline='From messy registration rows to a roster, a seat, and a badge.',color='#bd6338',
        primary='registration_ref',fields=[
            field('registration_ref','Registration reference','REG-011'),field('full_name','Attendee name','Avery Example'),
            field('email','Email','avery@example.invalid','email'),field('phone','Phone','+1 555 555 0146',required=False),
            field('session','Session','Repair café'),field('event_date','Event date','2026-10-10 10:00'),
            field('capacity','Session capacity',3,'number'),field('organization','Organizer','Gather Workshop')],
        stage_fields=[['registration_ref','full_name','email','phone','session'],['registration_ref','full_name','email','session','event_date','capacity'],['registration_ref','full_name','email','session','event_date','organization']],
        keys=['registration_ref','registration_ref','registration_ref'],action='checkin',action_label='Check in attendee',action_fields=[]),
}

# Per-destination field renames. The three apps call the same concept by different names; for field k, the app at
# stage i stores it under ALIASES[k][i] (fields not listed keep their own key in every app). This is what makes the
# "mapping" of each target meaningful: source key -> destination key.
ALIASES = {
    'full_name':['display_name','contact_name','addressee'],
    'email':['email','contact_email','delivery_email'],
    'phone':['phone','contact_phone','recipient_phone'],
    'street':['street','site_address','billing_address'],
    'customer_ref':['customer_ref','external_customer_ref','account_ref'],
}

# Enrich every scenario with catalog content and build its three destination targets.
# target.mapping : {canonical field -> that app's own field name}; target.primary : the field used as external key.
for key, scene in DEFINITIONS.items():
    scene['id'] = key
    scene['story'] = CATALOG[key]['story']
    scene['actor'] = CATALOG[key]['actor']
    scene['rules'] = CATALOG[key]['rules']
    scene['manual_steps'] = CATALOG[key]['manual']
    scene['scale'] = CATALOG[key]['scale']
    scene['targets'] = []
    for i, name in enumerate(CATALOG[key]['apps']):
        # i is the stage index (0..2) so each app picks its own alias for shared fields.
        mapping = {k: ALIASES.get(k, [k,k,k])[i] for k in scene['stage_fields'][i]}
        scene['targets'].append({'id':f'{key}-{i}', 'index':i, 'name':name,
            'color':['#137e72','#bb7636','#8057d5'][i], 'mapping':mapping,
            'primary':scene['keys'][i], 'output':CATALOG[key]['outputs'][i]})


def defaults(scenario):
    """Return {field key: default value} for a scenario, used to pre-fill forms and to fill gaps in partial records."""
    return {f['key']: f['default'] for f in DEFINITIONS[scenario]['fields']}


def public_config():
    """Return all scenario definitions as a list for the /api/config endpoint (the UI renders forms from this)."""
    return list(DEFINITIONS.values())
