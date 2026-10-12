#!/usr/bin/env python3
"""Relayworks: local portal + separately authenticated workplace HTTP API."""
import argparse
import base64
import csv
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import io
import json
import mimetypes
from pathlib import Path
import secrets
import shutil
import signal
import threading
import time
import traceback
import urllib.parse
import uuid
import zipfile

from config import ROOT, DEFINITIONS, defaults, public_config
from data_tools import (SAMPLE_SHEET, google_sheet, openf1, import_file, messy_matrix,
                        normalize_table, suggest_mapping, pdf_bytes, xlsx_bytes, now)
from engine import Engine, Workplaces, Problem, validate, encoded


class Server(ThreadingHTTPServer):
    daemon_threads=True
    allow_reuse_address=True


class Handler(BaseHTTPRequestHandler):
    protocol_version='HTTP/1.1'

    def log_message(self,fmt,*args):
        if self.server.verbose:super().log_message(fmt,*args)

    def send(self,data,status=200,content_type='application/json',filename=None):
        if content_type=='application/json':data=encoded(data).encode()
        elif isinstance(data,str):data=data.encode()
        self.send_response(status)
        self.send_header('Content-Type',content_type)
        self.send_header('Content-Length',str(len(data)))
        self.send_header('X-Content-Type-Options','nosniff')
        self.send_header('Referrer-Policy','no-referrer')
        self.send_header('Cache-Control','no-store')
        if filename:self.send_header('Content-Disposition',f'attachment; filename="{filename}"')
        if content_type.startswith('text/html'):
            self.send_header('Content-Security-Policy',"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'; form-action 'self'")
        self.end_headers()
        try:self.wfile.write(data)
        except (BrokenPipeError,ConnectionResetError):pass

    def body(self):
        length=int(self.headers.get('Content-Length','0'))
        if length<0 or length>12_000_000:raise Problem('Request exceeds the 12 MB demo limit.',413)
        value=json.loads(self.rfile.read(length) or b'{}')
        if not isinstance(value,dict):raise Problem('A JSON object is required.')
        return value

    def do_GET(self):self.handle_route('GET')
    def do_POST(self):self.handle_route('POST')

    def handle_route(self,method):
        try:
            # Bound to loopback, with Host/Origin checks against browser DNS rebinding.
            host=self.headers.get('Host','')
            expected={f'127.0.0.1:{self.server.server_port}',f'localhost:{self.server.server_port}'}
            if host not in expected:raise Problem('Use the local showcase address.',403)
            if method=='POST' and self.headers.get('Origin') and self.headers['Origin'] not in {'http://'+h for h in expected}:
                raise Problem('Cross-origin writes are not allowed.',403)
            parsed=urllib.parse.urlsplit(self.path)
            path=urllib.parse.unquote(parsed.path);query=urllib.parse.parse_qs(parsed.query)
            body=self.body() if method=='POST' else {}
            if self.server.role=='workplaces':return self.workplace(method,path,body)
            return self.portal(method,path,query,body)
        except Problem as error:self.send({'error':str(error),'details':error.details},error.status)
        except (ValueError,KeyError,TypeError,zipfile.BadZipFile) as error:self.send({'error':str(error)},422)
        except Exception:
            traceback.print_exc();self.send({'error':'The local service could not complete that request. See its terminal log.'},500)

    def workplace(self,method,path,body):
        if self.headers.get('Authorization')!='Bearer '+self.server.token:raise Problem('A local API grant is required.',401)
        parts=path.strip('/').split('/');stores=self.server.stores
        if len(parts)<3 or parts[0]!='v1':raise Problem('Unknown endpoint.',404)
        app_id=parts[1]
        if parts[2]=='state' and method=='GET':return self.send(stores.state(app_id))
        if parts[2]=='settings' and method=='POST':return self.send(stores.settings(app_id,body))
        if parts[2]=='reset' and method=='POST':stores.reset(app_id);return self.send({'reset':True})
        if parts[2]=='records':
            if method=='POST':return self.send(stores.save(app_id,body),201)
            if len(parts)==4:return self.send({'record':stores.get(app_id,parts[3])})
            return self.send({'records':stores.list(app_id)})
        raise Problem('Unknown endpoint.',404)

    def portal(self,method,path,query,body):
        engine=self.server.engine
        p=path.strip('/').split('/')
        if path=='/api/config':
            return self.send({'scenarios':public_config(),'sample_sheet':SAMPLE_SHEET,'tools':{t:bool(shutil.which(t)) for t in ['pdftotext','pdftoppm','tesseract','libreoffice']},'workplace_port':self.server.workplace_port,'data_dir':str(engine.directory)})
        if path=='/api/dashboard':return self.send(engine.dashboard())
        if path=='/api/preview' and method=='POST':
            scenario=body['scenario'];data=validate(scenario,body['data'])
            return self.send({'data':data,'targets':[dict(t,payload={v:data[k] for k,v in t['mapping'].items()}) for t in DEFINITIONS[scenario]['targets']]})
        if path=='/api/runs' and method=='POST':
            return self.send(engine.enqueue(body['scenario'],body['data'],body.get('source'),body.get('kind','intake'),body.get('action'),body.get('event_id')),202)
        if len(p)>=3 and p[:2]==['api','runs']:
            run_id=p[2]
            if len(p)==3:return self.send(engine.run(run_id))
            if p[3]=='resume' and method=='POST':return self.send({'run':engine.resume(run_id)},202)
            if p[3]=='report.pdf':return self.send(engine.report(run_id),content_type='application/pdf',filename='workflow-'+run_id+'.pdf')
            if p[3]=='calendar.ics':return self.send(engine.calendar(run_id),content_type='text/calendar; charset=utf-8',filename='event-'+run_id+'.ics')
            if p[3]=='report.xlsx':
                run=engine.run(run_id);matrix=[['Destination','Record ID','Field','Value']]
                for out in run['outputs']:
                    matrix.extend([out['app_id'],out['record']['id'],k,str(v)] for k,v in out['record']['payload'].items() if not k.startswith('_'))
                return self.send(xlsx_bytes(matrix),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',filename='workflow-'+run_id+'.xlsx')
            if p[3]=='evidence.zip':return self.evidence_zip(run_id)
        if path=='/api/reset' and method=='POST':
            scenario=body['scenario']
            if scenario not in DEFINITIONS:raise Problem('Unknown scenario.',404)
            with engine.lock:
                with engine.db() as db:
                    if db.execute("SELECT 1 FROM runs WHERE scenario=? AND status IN ('queued','running')",(scenario,)).fetchone():raise Problem('Let the active job finish before clearing its workplaces.',409)
                    db.execute("UPDATE runs SET status='archived',message='Workplaces reset for another demonstration.' WHERE scenario=? AND status!='archived'",(scenario,))
                engine.api('POST',f'/v1/{scenario}/reset',{})
                engine.set_setting('generation:'+scenario,engine.setting('generation:'+scenario,0)+1)
            return self.send({'reset':True})
        if len(p)>=4 and p[:2]==['api','workplaces']:
            app_id=p[2];scenario,index=app_id.rsplit('-',1);scene=DEFINITIONS[scenario];target=scene['targets'][int(index)]
            if p[3]=='settings' and method=='POST':return self.send(engine.api('POST',f'/v1/{app_id}/settings',body))
            if p[3]=='records':
                if method=='POST':
                    supplied=body['data'];partial={**defaults(scenario),**supplied};normalized=validate(scenario,partial)
                    for key in target['mapping']:
                        if key not in supplied:normalized[key]=''
                    payload={v:normalized[k] for k,v in target['mapping'].items()}
                    result=engine.api('POST',f'/v1/{app_id}/records',{'operation_id':'manual-'+str(uuid.uuid4()),'external_key':str(normalized[target['primary']]),'payload':payload,'kind':'intake','source':{'kind':'manual entry'}})
                    count=sum(str(v).strip()!='' for v in supplied.values())
                    with engine.db() as db:db.execute('INSERT INTO manual(scenario,app_id,field_count,record_id,created) VALUES(?,?,?,?,?)',(scenario,app_id,count,result['record']['id'],now()))
                    return self.send(result,201)
                suffix='/'+p[4] if len(p)==5 else ''
                return self.send(engine.api('GET',f'/v1/{app_id}/records'+suffix))
            if p[3]=='export.csv':
                records=engine.api('GET',f'/v1/{app_id}/records')['records'];cols=list(target['mapping'].values())+['status']
                matrix=[cols]+[[r['payload'].get(k,'') for k in cols] for r in records]
                return self.send(csv_bytes(matrix),content_type='text/csv; charset=utf-8',filename=app_id+'.csv')
            if p[3]=='document.pdf' and len(p)==5:
                record=engine.api('GET',f'/v1/{app_id}/records/'+p[4])['record'];payload=record['payload']
                templates={'hvac':['Customer profile','Work order','Invoice draft'],'sports':['Source report','Session schedule','Personal briefing'],'legal':['Matter cover sheet','Client information packet','Appointment checklist'],'clinic':['Administrative patient record','Appointment confirmation','Intake packet'],'retail':['Receiving receipt','Stock movement','Availability report'],'reseller':['Item catalog card','Listing draft','Packing slip' if payload.get('buyer') else 'Sale paperwork template'],'property':['Repair request','Contractor work order','Owner statement'],'events':['Registration record','Seat allocation','Attendee badge']}
                heading=templates[scenario][int(index)]
                lines=[f"Reference: {record['external_key']}",f"Record ID: {record['id']}",f"Status: {payload.get('status')}",'']
                for f in scene['fields']:
                    dest=target['mapping'].get(f['key'])
                    if dest:lines.append(f"{f['label']}: {payload.get(dest,'')}")
                lines+=['']+[f"{k.replace('_',' ').title()}: {v}" for k,v in payload.items() if not k.startswith('_') and k not in target['mapping'].values() and k!='status']
                if scenario=='hvac' and int(index)==2:lines+=['','Diagnostic fee + approved labor hours x hourly rate + approved parts.','Draft for review. No payment has been charged.']
                return self.send(pdf_bytes(scene['company']+' / '+heading,lines),content_type='application/pdf',filename=app_id+'-'+record['id']+'.pdf')
        if path=='/api/sources' and method=='GET':return self.send({'sources':engine.sources()})
        if len(p)==3 and p[:2]==['api','sources']:
            name=p[2]
            if method=='GET':return self.send(engine.source(name))
            if name=='fixture':
                scene=DEFINITIONS[body['scenario']];source=normalize_table(messy_matrix(scene),scene['company']+' · messy workbook','generated messy workbook')
                source['note']='Created here with synthetic people and business facts. The mess is deliberate and reproducible.'
            elif name=='google':source=google_sheet(body.get('url') or SAMPLE_SHEET)
            elif name=='openf1':source=openf1(body.get('session','9158'),body.get('driver','1'))
            elif name=='upload':source=import_file(base64.b64decode(body['base64'],validate=True),Path(body['name']).name)
            elif name in ['recorded-google','recorded-openf1']:
                snapshot=ROOT/'fixtures/public'/(name.removeprefix('recorded-')+'.json')
                if not snapshot.exists():raise Problem('No verified recording is available yet.',404)
                source=json.loads(snapshot.read_text());source.pop('id',None)
                source.update(original_kind=source['kind'],kind='recorded '+source['kind'],replayed_at=now(),note='Recorded provider response from '+source['fetched_at']+'. This is a replay, not a fresh network request.')
            else:raise Problem('Unknown source connector.',404)
            return self.send(engine.add_source(source),201)
        if path=='/api/mapping' and method=='POST':
            scene=DEFINITIONS[body['scenario']];source=engine.source(body['source_id']);row=source['rows'][int(body.get('row',0))]
            mapping=body.get('mapping') or suggest_mapping(source['columns'],scene['fields'])
            engine.set_setting('mapping:'+body['scenario']+':'+ '|'.join(source['columns']),mapping)
            data=defaults(body['scenario']);data.update({k:row['values'].get(col,'') for k,col in mapping.items() if col})
            # Public class data has no email or business ID. Generate clearly synthetic missing facts.
            if 'Google Sheets fetch' in source['kind']:
                primary=scene['primary']
                if not mapping.get(primary):data[primary]='SHEET-'+str(row['row_number'])
                if 'email' in data and not mapping.get('email'):data['email']='sheet-row-'+str(row['row_number'])+'@example.invalid'
            if source.get('extraction_tool') or row['issues']:
                data['_review_reason']='Review extracted values and resolve source issues: '+ '; '.join(row['issues'] or ['Check the original document.'])
            provenance={k:source[k] for k in ['id','kind','name','fetched_at','url','request_url','http_status','extraction_tool','raw_hash','requests'] if k in source}
            provenance.update(row_number=row['row_number'],mapped_fields=list(mapping),synthetic_defaults=[f['key'] for f in scene['fields'] if not mapping.get(f['key'])])
            return self.send({'data':data,'mapping':mapping,'source':provenance,'issues':row['issues'],'changes':row['changes']})
        if len(p)==4 and p[:2]==['api','sources'] and p[3]=='mapping':
            source=engine.source(p[2]);scenario=query.get('scenario',['hvac'])[0]
            default=suggest_mapping(source['columns'],DEFINITIONS[scenario]['fields'])
            return self.send({'mapping':engine.setting('mapping:'+scenario+':'+ '|'.join(source['columns']),default)})
        if path=='/api/schedules':
            if method=='POST':
                config={k:body.get(k) for k in ['enabled','kind','url','scenario','mapping']}
                config['interval']=max(60,int(body.get('interval',300)))
                if config['kind'] not in ['google','openf1'] or config['scenario'] not in DEFINITIONS:raise Problem('Choose a supported source and workflow.')
                config.update(id=str(uuid.uuid4()),last_run=None,next_run=time.time()+config['interval'],message='Waiting for the first scheduled pull.')
                engine.set_setting('schedule',config)
            return self.send(engine.setting('schedule',{'enabled':False}))
        if path=='/api/evidence':
            manifest=ROOT/'evidence/manifest.json'
            return self.send(json.loads(manifest.read_text()) if manifest.exists() else {'captures':[]})
        if path.startswith('/fixtures/'):
            filename=p[-1];scenario,ext=filename.rsplit('.',1);scene=DEFINITIONS[scenario]
            if ext=='pdf':return self.send(pdf_bytes(scene['company']+' / Intake',[f"{f['label']}: {f['default']}" for f in scene['fields']]),content_type='application/pdf',filename=filename)
            matrix=messy_matrix(scene)
            if ext=='xlsx':return self.send(xlsx_bytes(matrix),content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',filename=filename)
            if ext=='csv':return self.send(csv_bytes(matrix),content_type='text/csv; charset=utf-8',filename=filename)
        if path in ['/','/workplace']:return self.static(ROOT/'web','index.html')
        if path in ['/START_HERE.html','/THE_WORKS.html','/BUSINESS_PLAYBOOK.html']:return self.static(ROOT,path[1:])
        if path=='/web/books.js':return self.static(ROOT/'web','books.js')
        for prefix,directory in [('/assets/',ROOT/'web'),('/diagrams/',ROOT/'diagrams'),('/docs/',ROOT/'docs'),('/evidence/',ROOT/'evidence'),('/books/',ROOT/'books')]:
            if path.startswith(prefix):return self.static(directory,path[len(prefix):])
        raise Problem('Page not found.',404)

    def static(self,root,relative):
        file=(root/relative).resolve()
        if not file.is_relative_to(root.resolve()) or not file.is_file():raise Problem('File not found.',404)
        mime=mimetypes.guess_type(file.name)[0] or 'application/octet-stream'
        if mime.startswith('text/'):mime+='; charset=utf-8'
        return self.send(file.read_bytes(),content_type=mime)

    def evidence_zip(self,run_id):
        engine=self.server.engine;run=engine.run(run_id);mem=io.BytesIO()
        with zipfile.ZipFile(mem,'w',zipfile.ZIP_DEFLATED) as archive:
            archive.writestr('run-and-http-trace.json',encoded(run))
            archive.writestr('workflow-packet.pdf',engine.report(run_id))
            archive.write(ROOT/'diagrams'/f"{run['scenario']}.png",'workflow.png')
            archive.write(ROOT/'diagrams/showcase.archi.json','editable-workflows.archi.json')
            for file in (ROOT/'evidence').glob(run['scenario']+'-*.png'):archive.write(file,'screenshots/'+file.name)
            archive.writestr('READ-ME.txt','The screenshots show an actual scripted demonstration captured at the time listed in evidence/manifest.json. They are distinct from the current run JSON and PDF. Business people and records are synthetic. External sources carry their own provenance. No external messages or payments are sent.')
            if (ROOT/'evidence/manifest.json').exists():archive.write(ROOT/'evidence/manifest.json','capture-manifest.json')
        return self.send(mem.getvalue(),content_type='application/zip',filename='relayworks-'+run_id+'.zip')


def csv_bytes(matrix):
    out=io.StringIO();writer=csv.writer(out)
    # Export as values; prevent spreadsheet applications executing user-supplied formulas.
    for row in matrix:writer.writerow(["'"+str(v) if str(v).lstrip().startswith(('=','+','-','@')) else v for v in row])
    return out.getvalue().encode('utf-8-sig')


def scheduler(engine,stop):
    while not stop.wait(2):
        config=engine.setting('schedule',{})
        if not config.get('enabled') or time.time()<config.get('next_run',0):continue
        try:
            source=engine.add_source(google_sheet(config.get('url') or SAMPLE_SHEET) if config['kind']=='google' else openf1())
            scene=DEFINITIONS[config['scenario']];mapping=config.get('mapping') or suggest_mapping(source['columns'],scene['fields'])
            queued=0;held=0
            for row in source['rows'][:100]:
                if row['duplicate'] or row['issues']:held+=1;continue
                data=defaults(config['scenario']);data.update({k:row['values'][col] for k,col in mapping.items() if col in row['values']})
                if config['kind']=='google':
                    if not mapping.get(scene['primary']):data[scene['primary']]='SHEET-'+str(row['row_number'])
                    if 'email' in data and not mapping.get('email'):data['email']='sheet-row-'+str(row['row_number'])+'@example.invalid'
                try:
                    engine.enqueue(config['scenario'],data,{'kind':'scheduled '+source['kind'],'source_id':source['id'],'row_number':row['row_number'],'fetched_at':source['fetched_at'],'synthetic_defaults':[f['key'] for f in scene['fields'] if not mapping.get(f['key'])]});queued+=1
                except Problem:held+=1
            config['message']=f'{queued} rows submitted (unchanged input deduplicates); {held} held for review.'
        except Exception as error:config['message']='Refresh stopped: '+str(error)
        config.update(last_run=now(),next_run=time.time()+config['interval'])
        # An in-flight fetch must not turn a schedule back on after the user disables it.
        current=engine.setting('schedule',{})
        if current.get('enabled') and current.get('id')==config.get('id'):engine.set_setting('schedule',config)


def main():
    parser=argparse.ArgumentParser(description='Run the free local automation showcase.')
    parser.add_argument('--port',type=int,default=8765);parser.add_argument('--workplace-port',type=int,default=8766)
    parser.add_argument('--data-dir',default=str(ROOT/'runtime'));parser.add_argument('--verbose',action='store_true')
    args=parser.parse_args();token=secrets.token_urlsafe(32)
    stores=Workplaces(Path(args.data_dir)/'workplaces')
    api=Server(('127.0.0.1',args.workplace_port),Handler);api.role='workplaces';api.stores=stores;api.token=token;api.verbose=args.verbose
    threading.Thread(target=api.serve_forever,daemon=True).start()
    engine=Engine(args.data_dir,f'http://127.0.0.1:{args.workplace_port}',token)
    portal=Server(('127.0.0.1',args.port),Handler);portal.role='portal';portal.engine=engine;portal.verbose=args.verbose;portal.workplace_port=args.workplace_port
    stop=threading.Event();threading.Thread(target=scheduler,args=(engine,stop),daemon=True).start()
    print(f'Relayworks ready: http://127.0.0.1:{args.port}\n24 independent workplace stores · local API on {args.workplace_port}\nData: {args.data_dir}',flush=True)
    try:portal.serve_forever()
    except KeyboardInterrupt:pass
    finally:stop.set();portal.server_close();api.shutdown();api.server_close();engine.pool.shutdown(wait=True)


if __name__=='__main__':main()
