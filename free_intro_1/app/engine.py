"""Persistent orchestration and independent workplace stores."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from decimal import Decimal, InvalidOperation
from datetime import datetime, timedelta, timezone
import hashlib
import json
import math
from pathlib import Path
import re
import sqlite3
import threading
import time
import urllib.error
import urllib.request
import uuid
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from config import DEFINITIONS
from data_tools import now, pdf_bytes, xlsx_bytes


class Problem(Exception):
    def __init__(self, message, status=400, details=None):
        super().__init__(message);self.status=status;self.details=details


@contextmanager
def connection(path):
    db=sqlite3.connect(path,timeout=15)
    db.row_factory=sqlite3.Row
    db.execute('PRAGMA foreign_keys=ON')
    try:
        yield db
        db.commit()
    except BaseException:
        db.rollback();raise
    finally: db.close()


def encoded(value):
    return json.dumps(value,ensure_ascii=False,sort_keys=True,allow_nan=False)


def fingerprint(value):
    return hashlib.sha256(encoded(value).encode()).hexdigest()


def validate(scenario, supplied, kind='intake', action=None):
    scene=DEFINITIONS[scenario];data={};issues=[]
    for f in scene['fields']:
        value=supplied.get(f['key'],'')
        if isinstance(value,(dict,list)):issues.append(f"{f['label']}: use a single value");continue
        if isinstance(value,str):value=value.strip()
        if value=='' or value is None:
            if f['required']:issues.append(f"{f['label']} is required")
            data[f['key']]='';continue
        if f['type']=='number':
            try:
                number=Decimal(str(value))
                if not number.is_finite() or number<0 or number>1_000_000:raise InvalidOperation
                if f['key'] in ['quantity','reserved','capacity','laps'] and number!=int(number):raise InvalidOperation
                value=float(number)
            except InvalidOperation:issues.append(f"{f['label']}: enter a non-negative number");continue
        else:
            value=str(value)
            if len(value)>1500:issues.append(f"{f['label']} is too long")
        if f['type']=='email' and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',str(value)):
            issues.append(f"{f['label']} needs a valid address")
        if f['key'] in ['slot','appointment','event_date','birth_date'] and '/' in str(value):
            issues.append(f"{f['label']}: replace the ambiguous date with YYYY-MM-DD")
        if f['key'] in ['slot','appointment','event_date','birth_date'] and '/' not in str(value):
            try:datetime.fromisoformat(str(value).replace('Z','+00:00'))
            except ValueError:issues.append(f"{f['label']}: enter an ISO date, such as 2026-10-06 10:00")
        data[f['key']]=value
    review_reason=supplied.get('_review_reason','')
    if scenario=='legal' and str(data.get('other_party','')).lower()=='existing demo client':
        review_reason='Possible party match. Record the reviewer decision before creating the matter packet.'
    if review_reason and not supplied.get('_review_confirmed'):
        issues.append(review_reason)
    data['_review_confirmed']=bool(supplied.get('_review_confirmed'))
    if review_reason:data['_review_reason']=str(review_reason)[:500]
    if scenario=='events' and data.get('capacity')==0:issues.append('Session capacity must be at least 1')
    if scenario=='sports':
        try:ZoneInfo(str(data.get('timezone','')))
        except (ZoneInfoNotFoundError,ValueError):issues.append('Choose a valid timezone, such as America/Phoenix.')
    if scenario=='retail' and str(data.get('sku','')).upper() not in ['FLT-20','KIT-07','BOLT-12']:
        issues.append('SKU needs mapping. Demo inventory accepts FLT-20, KIT-07, or BOLT-12.')
    if kind=='invoice' and action and action.get('job_reference')!=data.get('ticket_ref'):
        issues.append('The invoice job reference does not match this repair ticket.')
    if kind=='invoice' and action:
        try:
            if float(action.get('invoice_total',0))>float(data.get('estimate',0)) and not action.get('approved_overage'):
                issues.append('Invoice exceeds the approved estimate. Review the amount before matching it.')
        except (ValueError,TypeError):issues.append('Invoice total must be a number.')
    if issues:raise Problem('Review the intake before running.',422,issues)
    return data


class Workplaces:
    def __init__(self, directory):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        for scene in DEFINITIONS.values():
            for target in scene['targets']:
                with self.db(target['id']) as db:
                    db.executescript('''
                    CREATE TABLE IF NOT EXISTS records(id TEXT PRIMARY KEY, external_key TEXT UNIQUE NOT NULL, payload TEXT NOT NULL, revision INTEGER NOT NULL DEFAULT 1, created TEXT, updated TEXT);
                    CREATE TABLE IF NOT EXISTS operations(id TEXT PRIMARY KEY, request_hash TEXT NOT NULL, response TEXT NOT NULL);
                    CREATE TABLE IF NOT EXISTS business_events(id TEXT PRIMARY KEY, request_hash TEXT NOT NULL);
                    CREATE TABLE IF NOT EXISTS reservations(resource TEXT PRIMARY KEY, external_key TEXT UNIQUE NOT NULL);
                    CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY, value TEXT NOT NULL);
                    INSERT OR IGNORE INTO settings VALUES('online','true');
                    INSERT OR IGNORE INTO settings VALUES('authorized','true');
                    ''')

    def db(self,app_id):
        if not any(app_id==t['id'] for s in DEFINITIONS.values() for t in s['targets']):raise Problem('Unknown workplace.',404)
        return connection(self.directory/(app_id+'.sqlite3'))

    def state(self,app_id):
        with self.db(app_id) as db:
            settings={r['key']:json.loads(r['value']) for r in db.execute('SELECT * FROM settings')}
            settings['count']=db.execute('SELECT COUNT(*) FROM records').fetchone()[0]
        return settings

    def settings(self,app_id,changes):
        with self.db(app_id) as db:
            for key,value in changes.items():
                if key not in ['online','authorized'] or not isinstance(value,bool):raise Problem('Invalid connection setting.')
                db.execute('UPDATE settings SET value=? WHERE key=?',(json.dumps(value),key))
        return self.state(app_id)

    def list(self,app_id):
        with self.db(app_id) as db:
            return [self.unpack(row) for row in db.execute('SELECT * FROM records ORDER BY updated DESC')]

    def get(self,app_id,record_id):
        with self.db(app_id) as db:
            row=db.execute('SELECT * FROM records WHERE id=?',(record_id,)).fetchone()
            if row is None:raise Problem('Record not found.',404)
            return self.unpack(row)

    @staticmethod
    def unpack(row):
        data=dict(row);data['payload']=json.loads(data['payload']);return data

    def reset(self,scenario):
        for target in DEFINITIONS[scenario]['targets']:
            with self.db(target['id']) as db:
                for table in ['records','operations','business_events','reservations']:db.execute('DELETE FROM '+table)
                db.execute("UPDATE settings SET value='true'")

    def save(self,app_id,request):
        scenario,index=app_id.rsplit('-',1);index=int(index);scene=DEFINITIONS[scenario];target=scene['targets'][index]
        state=self.state(app_id)
        if not state['online']:raise Problem(f"{target['name']} is temporarily unavailable.",503)
        if not state['authorized']:raise Problem(f"Access to {target['name']} has been revoked. Grant local API access to resume.",403)
        payload=request.get('payload',{});key=str(request.get('external_key','')).strip()
        operation_id=str(request.get('operation_id','')).strip();kind=request.get('kind','intake')
        if not key or not operation_id or not isinstance(payload,dict):raise Problem('Record key, operation ID, and payload are required.')
        canonical={k:payload.get(v,'') for k,v in target['mapping'].items()}
        for f in scene['fields']:
            if f['key'] in canonical and f['required'] and canonical[f['key']] in ['',None]:raise Problem(f"{f['label']} is required by {target['name']}.",422)
        signature=fingerprint(request)
        with self.db(app_id) as db:
            db.execute('BEGIN IMMEDIATE')
            previous_op=db.execute('SELECT * FROM operations WHERE id=?',(operation_id,)).fetchone()
            if previous_op:
                if previous_op['request_hash']!=signature:raise Problem('Operation ID was reused with different data.',409)
                result=json.loads(previous_op['response']);result['reused']=True;return result
            old=db.execute('SELECT * FROM records WHERE external_key=?',(key,)).fetchone()
            old_payload=json.loads(old['payload']) if old else {}
            if kind in ['completion','sale','invoice','checkin']:
                event_id=str(request.get('action',{}).get('event_id',''))
                if not event_id:raise Problem('Follow-up actions require a stable event reference.',422)
                event_key=kind+':'+event_id
                event_hash=fingerprint({'external_key':key,'payload':payload,'action':request.get('action',{})})
                prior_event=db.execute('SELECT request_hash FROM business_events WHERE id=?',(event_key,)).fetchone()
                if prior_event and prior_event[0]!=event_hash:raise Problem('This event reference was already applied with different data.',409)
                db.execute('INSERT OR IGNORE INTO business_events VALUES(?,?)',(event_key,event_hash))
            if old_payload.get('status') in ['Sold','Completed'] and kind=='intake' and not (scenario=='hvac' and index==0):
                raise Problem('This item or job is already completed. Use a new reference for new work.',409)
            status='Saved'
            if index==1 and scenario in ['hvac','clinic']:
                resource=str(canonical.get('technician') or canonical.get('provider'))+'|'+str(canonical.get('slot'))
                reservation=db.execute('SELECT external_key FROM reservations WHERE resource=?',(resource,)).fetchone()
                if reservation and reservation[0]!=key:raise Problem('That appointment slot is already reserved. Choose another slot.',409)
                db.execute('DELETE FROM reservations WHERE external_key=?',(key,))
                db.execute('INSERT INTO reservations VALUES(?,?)',(resource,key));status='Scheduled'
            if scenario=='hvac' and index==2:
                fee=Decimal(str(canonical.get('fee',0)))
                payload['total_usd']=str(fee.quantize(Decimal('.01')));status='Draft'
                if kind=='completion':
                    action=request.get('action',{})
                    total=fee+Decimal(str(action['hours']))*Decimal(str(action['hourly_rate']))+Decimal(str(action['parts']))
                    payload.update(labor_hours=action['hours'],hourly_rate=action['hourly_rate'],parts_usd=action['parts'],total_usd=str(total.quantize(Decimal('.01'))))
            if kind=='completion' and scenario=='hvac' and index==1:status='Completed'
            if scenario=='hvac' and index==0:
                status='Active customer'
                history=old_payload.get('service_references',[])
                reference=request.get('business_reference')
                if reference and reference not in history:history=history+[reference]
                payload['service_references']=history
            if scenario=='legal':status=['Reviewed matter','Draft packet','Scheduled task'][index]
            if scenario=='clinic' and index!=1:status=['Registered','', 'Packet prepared'][index]
            if scenario=='retail':
                status=['Received','Stock updated','Available online'][index]
                if index==1:
                    receipt=str(canonical['receipt_ref']);event='receipt:'+receipt
                    business_hash=fingerprint({k:canonical[k] for k in ['receipt_ref','sku','quantity']})
                    prior=db.execute('SELECT request_hash FROM business_events WHERE id=?',(event,)).fetchone()
                    if prior and prior[0]!=business_hash:raise Problem('This receipt already changed stock. Use a new receipt reference for another delivery.',409)
                    addition=0 if prior else float(canonical['quantity'])
                    quantity=float(old_payload.get('stock_quantity',0))+addition
                    reserved=float(canonical.get('reserved',0))
                    if reserved>quantity:raise Problem('Reserved quantity exceeds stock on hand.',409)
                    payload.update(stock_quantity=quantity,available_quantity=quantity-reserved)
                    db.execute('INSERT OR IGNORE INTO business_events VALUES(?,?)',(event,business_hash))
            if scenario=='reseller':
                status=['In stock','Draft listing','Awaiting sale'][index]
                if index==0:payload['stock_quantity']=old_payload.get('stock_quantity',1)
                if kind=='sale':
                    if index==0:
                        if not old:raise Problem('Create the item before recording its sale.',409)
                        if old_payload.get('stock_quantity',0)<1:raise Problem('This unique item is already sold. A second sale cannot reserve it.',409)
                        payload['stock_quantity']=0
                    payload.update(request.get('action',{}));status=['Sold','Sold','Ready to pack'][index]
            if scenario=='property':
                status=['Open repair','Assigned','Awaiting invoice'][index]
                if kind=='invoice':payload.update(request.get('action',{}));status=['Completed','Completed','Invoice matched'][index]
            if scenario=='events':
                status=['Registered','Reserved','Badge ready'][index]
                if index==1:
                    others=[json.loads(r[0]) for r in db.execute('SELECT payload FROM records WHERE external_key<>?',(key,))]
                    occupied=sum(p.get('session')==canonical.get('session') and p.get('status') in ['Reserved','Checked in'] for p in others)
                    status='Waitlisted' if occupied>=float(canonical['capacity']) else 'Reserved'
                if index==2 and request.get('upstream_status')=='Waitlisted':status='Waitlisted'
                if kind=='checkin':
                    if old_payload.get('status')=='Waitlisted':raise Problem('A waitlisted attendee must receive a seat before check-in.',409)
                    status='Checked in'
            if scenario=='sports':
                status=['Source recorded','Schedule updated','Report ready'][index]
                if index==1:
                    start=datetime.fromisoformat(str(canonical['event_date']).replace('Z','+00:00'))
                    if start.tzinfo is None:start=start.replace(tzinfo=ZoneInfo(canonical['timezone']))
                    payload['local_start']=start.astimezone(ZoneInfo(canonical['timezone'])).isoformat()
            payload['status']=status
            if request.get('source'):payload['_source']=request['source']
            if request.get('links'):payload['_linked_records']=request['links']
            timestamp=now();record_id=old['id'] if old else str(uuid.uuid4())[:12]
            db.execute('''INSERT INTO records(id,external_key,payload,created,updated) VALUES(?,?,?,?,?)
                ON CONFLICT(external_key) DO UPDATE SET payload=excluded.payload,revision=records.revision+1,updated=excluded.updated''',
                (record_id,key,encoded(payload),timestamp,timestamp))
            record=self.unpack(db.execute('SELECT * FROM records WHERE id=?',(record_id,)).fetchone())
            result={'record':record,'created':not bool(old),'reused':False}
            db.execute('INSERT INTO operations VALUES(?,?,?)',(operation_id,signature,encoded(result)))
            return result


class Engine:
    def __init__(self,directory,workplace_url,token):
        self.directory=Path(directory);self.directory.mkdir(parents=True,exist_ok=True)
        self.path=self.directory/'coordinator.sqlite3';self.workplace_url=workplace_url;self.token=token
        self.pool=ThreadPoolExecutor(max_workers=3,thread_name_prefix='relay-workflow')
        self.locks={};self.lock=threading.RLock()
        with self.db() as db:
            db.executescript('''
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY,scenario TEXT, fingerprint TEXT UNIQUE,status TEXT,payload TEXT,source TEXT,kind TEXT,action TEXT,created TEXT,updated TEXT,elapsed_ms INTEGER DEFAULT 0,message TEXT DEFAULT '');
            CREATE TABLE IF NOT EXISTS steps(id INTEGER PRIMARY KEY AUTOINCREMENT,run_id TEXT,stage INTEGER,kind TEXT,method TEXT,path TEXT,status INTEGER,duration_ms INTEGER,data TEXT,created TEXT);
            CREATE TABLE IF NOT EXISTS sources(id TEXT PRIMARY KEY,data TEXT,created TEXT);
            CREATE TABLE IF NOT EXISTS manual(id INTEGER PRIMARY KEY AUTOINCREMENT,scenario TEXT,app_id TEXT,field_count INTEGER,record_id TEXT,created TEXT);
            CREATE TABLE IF NOT EXISTS settings(key TEXT PRIMARY KEY,value TEXT);
            ''')
            db.execute("UPDATE runs SET status='interrupted',message='The service restarted. Resume from the saved steps.' WHERE status IN ('queued','running')")

    def db(self):return connection(self.path)

    def api(self,method,path,data=None,run_id=None,stage=-1,kind='api'):
        started=time.monotonic();status=0;result={}
        req=urllib.request.Request(self.workplace_url+path,data=encoded(data).encode() if data is not None else None,
                headers={'Content-Type':'application/json','Authorization':'Bearer '+self.token},method=method)
        try:
            with urllib.request.urlopen(req,timeout=20) as response:status=response.status;result=json.load(response)
        except urllib.error.HTTPError as error:
            status=error.code
            with error:
                try:result=json.load(error)
                except ValueError:result={'error':'Destination returned an unreadable response.'}
        except urllib.error.URLError:
            result={'error':'The destination API could not be reached.'};status=503
        duration=round((time.monotonic()-started)*1000)
        if run_id:
            with self.db() as db:
                db.execute('INSERT INTO steps(run_id,stage,kind,method,path,status,duration_ms,data,created) VALUES(?,?,?,?,?,?,?,?,?)',
                    (run_id,stage,kind,method,path,status,duration,encoded({'request':data,'response':result}),now()))
        if status>=400:raise Problem(result.get('error','Destination operation failed.'),status,result.get('details'))
        return result

    def enqueue(self,scenario,data,source=None,kind='intake',action=None,event_id=None):
        with self.lock:return self._enqueue(scenario,data,source,kind,action,event_id)

    def _enqueue(self,scenario,data,source=None,kind='intake',action=None,event_id=None):
        if scenario not in DEFINITIONS:raise Problem('Unknown workflow.',404)
        action=action or {};normalized=validate(scenario,data,kind,action)
        allowed=['intake','completion','sale','invoice','checkin']
        if kind not in allowed or (kind!='intake' and kind!=DEFINITIONS[scenario]['action']):raise Problem('Unsupported workflow action.')
        if kind!='intake':
            if not event_id:raise Problem('An event reference is required to prevent duplicate actions.')
            for f in DEFINITIONS[scenario]['action_fields']:
                value=action.get(f['key'],'')
                if value in ['',None]:raise Problem(f"{f['label']} is required.",422)
                if f['type']=='number':
                    try:value=float(value)
                    except (ValueError,TypeError):raise Problem(f"{f['label']} must be numeric.",422)
                    if not math.isfinite(value) or value<0 or value>100000:raise Problem(f"Invalid {f['label']}.",422)
                action[f['key']]=value
        # Business-identical input deduplicates even if imported by two different routes.
        digest=fingerprint([scenario,self.setting('generation:'+scenario,0),normalized,kind,event_id,action])
        with self.db() as db:
            previous=db.execute('SELECT id,status FROM runs WHERE fingerprint=?',(digest,)).fetchone()
            if previous:return {'run':self.run(previous['id']),'reused':True}
            run_id=str(uuid.uuid4())[:12];timestamp=now()
            try:
                db.execute('INSERT INTO runs(id,scenario,fingerprint,status,payload,source,kind,action,created,updated) VALUES(?,?,?,?,?,?,?,?,?,?)',
                    (run_id,scenario,digest,'queued',encoded(normalized),encoded(source or {'kind':'synthetic demo fixture'}),kind,encoded(dict(action,event_id=event_id)),timestamp,timestamp))
            except sqlite3.IntegrityError:
                existing=db.execute('SELECT id FROM runs WHERE fingerprint=?',(digest,)).fetchone()
                return {'run':self.run(existing['id']),'reused':True}
        self.pool.submit(self.execute,run_id)
        return {'run':self.run(run_id),'reused':False}

    def resume(self,run_id):
        with self.lock:
            run=self.run(run_id)
            if run['status'] in ['complete','running','queued']:return run
            if run['status']=='archived':raise Problem('This run belongs to a reset workplace. Create a fresh run from its input.',409)
            with self.db() as db:db.execute("UPDATE runs SET status='queued',message='Resuming saved steps.' WHERE id=?",(run_id,))
            self.pool.submit(self.execute,run_id)
            return self.run(run_id)

    def run(self,run_id):
        with self.db() as db:
            row=db.execute('SELECT * FROM runs WHERE id=?',(run_id,)).fetchone()
            if not row:raise Problem('Run not found.',404)
            result=dict(row)
            for key in ['payload','source','action']:result[key]=json.loads(result[key])
            result['steps']=[dict(r) for r in db.execute('SELECT * FROM steps WHERE run_id=? ORDER BY id',(run_id,))]
        result.pop('fingerprint',None)
        for step in result['steps']:step['data']=json.loads(step['data'])
        result['outputs']=[{'app_id':DEFINITIONS[result['scenario']]['targets'][s['stage']]['id'],'record':s['data']['response']['record']} for s in result['steps'] if s['kind']=='verified' and s['status']==200]
        return result

    def execute(self,run_id):
        with self.lock:lock=self.locks.setdefault(run_id,threading.Lock())
        if not lock.acquire(False):return
        started=time.monotonic();prior_time=0;worked=False
        try:
            run=self.run(run_id)
            if run['status'] in ['complete','archived']:return
            scene=DEFINITIONS[run['scenario']];data=run['payload'];prior_time=run['elapsed_ms']
            worked=True
            with self.db() as db:db.execute("UPDATE runs SET status='running',message='',updated=? WHERE id=?",(now(),run_id))
            completed={s['stage']:s['data']['response'] for s in run['steps'] if s['kind']=='verified' and s['status']==200}
            if run['kind']=='checkin' and not completed:
                records=self.api('GET','/v1/events-1/records')['records']
                seat=next((r for r in records if r['external_key']==str(data['registration_ref'])),None)
                if not seat or seat['payload'].get('status')=='Waitlisted':
                    raise Problem('A reserved seat is required before check-in.',409)
            links={};last_status='';previous_record=None
            for i,target in enumerate(scene['targets']):
                if i in completed:
                    verified=completed[i]
                else:
                    payload={dest:data.get(src,'') for src,dest in target['mapping'].items()}
                    if run['scenario']=='retail' and i==2 and previous_record:
                        payload['stock_quantity']=previous_record['payload'].get('stock_quantity',0)
                        payload['available_quantity']=previous_record['payload'].get('available_quantity',0)
                    request={'operation_id':run_id+':'+str(i),'external_key':str(data[target['primary']]),
                             'payload':payload,'kind':run['kind'],'action':run['action'],'source':run['source'],
                             'links':dict(links),'upstream_status':last_status,'business_reference':data[scene['primary']]}
                    saved=self.api('POST',f"/v1/{target['id']}/records",request,run_id,i,'write')
                    verified=self.api('GET',f"/v1/{target['id']}/records/{saved['record']['id']}",None,run_id,i,'readback')
                    if verified['record']['payload']!=saved['record']['payload']:raise Problem('Destination read-back did not match the saved record.',409)
                    with self.db() as db:
                        db.execute("UPDATE steps SET kind='verified' WHERE id=(SELECT MAX(id) FROM steps WHERE run_id=? AND stage=? AND kind='readback' AND status=200)",(run_id,i))
                record=verified['record'];links[target['id']]=record['id'];last_status=record['payload'].get('status','');previous_record=record
            with self.db() as db:db.execute("UPDATE runs SET status='complete',message='All three destinations were saved and read back.',updated=? WHERE id=?",(now(),run_id))
        except Exception as error:
            message=str(error) if isinstance(error,Problem) else 'An unexpected processing error occurred. Saved steps can be resumed.'
            if not isinstance(error,Problem):print(f'Workflow {run_id}: {type(error).__name__}: {error}',flush=True)
            with self.db() as db:db.execute("UPDATE runs SET status='needs_attention',message=?,updated=? WHERE id=?",(message,now(),run_id))
        finally:
            if worked:
                with self.db() as db:db.execute('UPDATE runs SET elapsed_ms=?,updated=? WHERE id=?',(prior_time+round((time.monotonic()-started)*1000),now(),run_id))
            lock.release()

    def setting(self,key,default=None):
        with self.db() as db:row=db.execute('SELECT value FROM settings WHERE key=?',(key,)).fetchone()
        return json.loads(row[0]) if row else default

    def set_setting(self,key,value):
        with self.db() as db:db.execute('INSERT INTO settings VALUES(?,?) ON CONFLICT(key) DO UPDATE SET value=excluded.value',(key,encoded(value)))

    def sources(self):
        with self.db() as db:return [dict(json.loads(r['data']),id=r['id']) for r in db.execute('SELECT * FROM sources ORDER BY created DESC')]

    def add_source(self,source):
        source_id=str(uuid.uuid4())[:12]
        with self.db() as db:db.execute('INSERT INTO sources VALUES(?,?,?)',(source_id,encoded(source),now()))
        return dict(source,id=source_id)

    def source(self,source_id):
        with self.db() as db:
            row=db.execute('SELECT * FROM sources WHERE id=?',(source_id,)).fetchone()
        if not row:raise Problem('Source not found.',404)
        return dict(json.loads(row['data']),id=source_id)

    def dashboard(self):
        with self.db() as db:
            runs=[dict(r) for r in db.execute('SELECT id,scenario,status,kind,created,elapsed_ms,message FROM runs ORDER BY created DESC LIMIT 100')]
            manual=[dict(r) for r in db.execute('SELECT * FROM manual ORDER BY id DESC LIMIT 200')]
        apps={}
        for key in DEFINITIONS:
            apps[key]=[self.api('GET',f"/v1/{t['id']}/state") for t in DEFINITIONS[key]['targets']]
        return {'runs':runs,'manual':manual,'apps':apps,
                'metrics':{'completed':sum(r['status']=='complete' for r in runs),'records':sum(a['count'] for values in apps.values() for a in values),'manual_fields':sum(r['field_count'] for r in manual)}}

    def report(self,run_id):
        run=self.run(run_id);scene=DEFINITIONS[run['scenario']]
        lines=[f"Run reference: {run_id}",f"Workflow: {scene['short']}",f"State: {run['status']}",f"Source: {run['source'].get('kind','')}",f"Created: {run['created']}",'']
        for f in scene['fields']:lines.append(f"{f['label']}: {run['payload'].get(f['key'],'')}")
        lines += ['', 'Verified destination records:']
        for result in run['outputs']:
            record=result['record'];lines.append(f"{result['app_id']}: {record['id']} / {record['payload'].get('status','')}")
            for key in ['total_usd','available_quantity','buyer','ship_to','invoice_total']:
                if key in record['payload']:lines.append(f"{key}: {record['payload'][key]}")
        return pdf_bytes(scene['company']+' / '+('Packing slip' if run['kind']=='sale' else 'Workflow packet'),lines)

    def calendar(self,run_id):
        run=self.run(run_id);data=run['payload'];scene=DEFINITIONS[run['scenario']]
        value=next((data[k] for k in ['slot','appointment','event_date'] if data.get(k)),None)
        if not value:raise Problem('This workflow does not have a calendar event.',422)
        start=datetime.fromisoformat(value.replace('Z','+00:00'))
        if start.tzinfo is None:start=start.replace(tzinfo=ZoneInfo(data.get('timezone','America/Phoenix')))
        def clean(v):return str(v).replace('\\','\\\\').replace('\n','\\n').replace('\r','').replace(';','\\;').replace(',','\\,')
        title=data.get('event_name') or data.get('session') or data.get('visit_type') or data.get('matter_type') or data.get('issue') or scene['short']
        lines=['BEGIN:VCALENDAR','VERSION:2.0','PRODID:-//Relayworks//Local Demo//EN','CALSCALE:GREGORIAN','BEGIN:VEVENT',
               'UID:'+clean(scene['id']+'-'+str(data[scene['primary']]))+'@relayworks.invalid',
               'DTSTAMP:'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
               'DTSTART:'+start.astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
               'DTEND:'+(start+timedelta(hours=1)).astimezone(timezone.utc).strftime('%Y%m%dT%H%M%SZ'),
               'SUMMARY:'+clean(title),'DESCRIPTION:'+clean('Local demonstration calendar event. Source: '+run['source'].get('kind','synthetic')),
               'STATUS:TENTATIVE','END:VEVENT','END:VCALENDAR']
        # Fold on UTF-8 octet boundaries per RFC 5545; never split an encoded character.
        folded=[]
        for line in lines:
            part=''
            for char in line:
                if len((part+char).encode())>74:folded.append(part);part=' '
                part+=char
            folded.append(part)
        return ('\r\n'.join(folded)+'\r\n').encode()
