"""Contract tests against both real local HTTP services and independent stores."""
import base64
import concurrent.futures
import io
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch
import urllib.error
import urllib.request
import zipfile

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'app'))
from config import DEFINITIONS, defaults
from data_tools import import_file, messy_matrix, pdf_bytes, xlsx_bytes, suggest_mapping, google_sheet
from engine import Engine, Workplaces
from server import Server, Handler


class Workflows(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='relay-test-')
        cls.api_server=Server(('127.0.0.1',0),Handler)
        cls.api_server.role='workplaces';cls.api_server.token='test-local-grant';cls.api_server.verbose=False
        cls.api_server.stores=Workplaces(Path(cls.tmp.name)/'workplaces')
        cls.engine=Engine(cls.tmp.name,f'http://127.0.0.1:{cls.api_server.server_port}',cls.api_server.token)
        cls.portal=Server(('127.0.0.1',0),Handler);cls.portal.role='portal';cls.portal.verbose=False
        cls.portal.engine=cls.engine;cls.portal.workplace_port=cls.api_server.server_port
        cls.base=f'http://127.0.0.1:{cls.portal.server_port}'
        for server in [cls.api_server,cls.portal]:threading.Thread(target=server.serve_forever,daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.engine.pool.shutdown(wait=True)
        for server in [cls.portal,cls.api_server]:server.shutdown();server.server_close()
        cls.tmp.cleanup()

    def request(self,path,data=None,expected=200):
        req=urllib.request.Request(self.base+path,data=json.dumps(data).encode() if data is not None else None,headers={'Content-Type':'application/json'})
        try:response=urllib.request.urlopen(req,timeout=15)
        except urllib.error.HTTPError as e:response=e
        with response:
            blob=response.read();self.assertEqual(response.status,expected,blob.decode(errors='replace')[:1000])
            return json.loads(blob) if 'application/json' in response.headers['Content-Type'] else blob

    def reset(self,s):self.request('/api/reset',{'scenario':s})
    def submit(self,s,data=None,**extra):return self.request('/api/runs',dict(scenario=s,data=data or defaults(s),**extra),202)
    def wait(self,run_id,status='complete'):
        deadline=time.monotonic()+8
        while time.monotonic()<deadline:
            run=self.request('/api/runs/'+run_id)
            if run['status'] not in ['running','queued']:
                self.assertEqual(run['status'],status,run['message']);return run
            time.sleep(.025)
        self.fail('Workflow did not finish.')

    def test_all_eight_workflows_write_and_read_back_three_independent_records(self):
        for s,scene in DEFINITIONS.items():
            with self.subTest(scenario=s):
                self.reset(s);result=self.submit(s);run=self.wait(result['run']['id'])
                self.assertEqual(len(run['outputs']),3)
                self.assertEqual([r['method'] for r in run['steps']],['POST','GET']*3)
                ids=set()
                for target,output in zip(scene['targets'],run['outputs']):
                    saved=self.request(f"/api/workplaces/{target['id']}/records/{output['record']['id']}")['record']
                    ids.add(saved['id'])
                    for key,dest in target['mapping'].items():self.assertEqual(str(saved['payload'][dest]),str(run['payload'][key]))
                    self.assertTrue((Path(self.tmp.name)/'workplaces'/(target['id']+'.sqlite3')).exists())
                self.assertEqual(len(ids),3)
                replay=self.submit(s);self.assertTrue(replay['reused']);self.assertEqual(replay['run']['id'],run['id'])

    def test_manual_entry_stays_in_its_own_app(self):
        self.reset('hvac');scene=DEFINITIONS['hvac'];data={k:defaults('hvac')[k] for k in scene['stage_fields'][0]}
        self.request('/api/workplaces/hvac-0/records',{'data':data},201)
        self.assertEqual(len(self.request('/api/workplaces/hvac-0/records')['records']),1)
        self.assertEqual(self.request('/api/workplaces/hvac-1/records')['records'],[])
        self.assertEqual(self.request('/api/workplaces/hvac-2/records')['records'],[])

    def test_grant_and_outage_resume_only_unfinished_steps(self):
        for setting,code in [('authorized',403),('online',503)]:
            with self.subTest(setting=setting):
                self.reset('hvac');self.request('/api/workplaces/hvac-1/settings',{setting:False})
                run=self.wait(self.submit('hvac')['run']['id'],'needs_attention')
                self.assertEqual(run['steps'][-1]['status'],code);self.assertEqual(len(run['outputs']),1)
                first=run['outputs'][0]['record'];self.request('/api/workplaces/hvac-1/settings',{setting:True})
                self.request('/api/runs/'+run['id']+'/resume',{},202)
                # resume is asynchronous; wait explicitly until complete
                deadline=time.monotonic()+5
                while time.monotonic()<deadline:
                    result=self.request('/api/runs/'+run['id'])
                    if result['status']=='complete':break
                    time.sleep(.025)
                self.assertEqual(result['status'],'complete');self.assertEqual(len(result['outputs']),3)
                saved=self.request('/api/workplaces/hvac-0/records/'+first['id'])['record']
                self.assertEqual(saved['revision'],1)

    def test_concurrent_appointments_cannot_double_book(self):
        self.reset('clinic')
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results=list(pool.map(lambda i:self.submit('clinic',dict(defaults('clinic'),patient_ref='RACE-'+str(i)))['run']['id'],range(2)))
        statuses=[]
        for rid in results:
            deadline=time.monotonic()+5
            while time.monotonic()<deadline:
                run=self.request('/api/runs/'+rid)
                if run['status'] not in ['queued','running']:break
                time.sleep(.025)
            statuses.append(run['status'])
        self.assertCountEqual(statuses,['complete','needs_attention'])
        self.assertEqual(len(self.request('/api/workplaces/clinic-1/records')['records']),1)

    def test_stock_delivery_business_identity_prevents_double_counting(self):
        self.reset('retail');first=self.wait(self.submit('retail')['run']['id'])
        changed=dict(defaults('retail'),supplier='Renamed supplier')
        second=self.wait(self.submit('retail',changed)['run']['id'])
        self.assertEqual(second['outputs'][1]['record']['payload']['stock_quantity'],12)
        third=self.wait(self.submit('retail',dict(changed,receipt_ref='REC-089'))['run']['id'])
        self.assertEqual(third['outputs'][1]['record']['payload']['stock_quantity'],24)
        bad=self.wait(self.submit('retail',dict(changed,quantity=999))['run']['id'],'needs_attention')
        self.assertIn('receipt already changed stock',bad['message'])

    def test_visit_completion_generates_exact_invoice_and_replays_safely(self):
        self.reset('hvac');self.wait(self.submit('hvac')['run']['id'])
        extra={'kind':'completion','action':{'hours':1.5,'hourly_rate':80,'parts':35},'event_id':'visit-done-1'}
        run=self.wait(self.submit('hvac',**extra)['run']['id'])
        self.assertEqual(run['outputs'][2]['record']['payload']['total_usd'],'250.00')
        self.assertTrue(self.submit('hvac',**extra)['reused'])
        self.assertEqual(self.request('/api/workplaces/hvac-2/records')['records'][0]['revision'],2)
        another=self.wait(self.submit('hvac',dict(defaults('hvac'),job_ref='RETURN-VISIT',slot='2026-10-09 14:00'))['run']['id'])
        self.assertEqual(another['outputs'][0]['record']['payload']['service_references'],['JOB-1042','RETURN-VISIT'])
        self.assertEqual(len(self.request('/api/workplaces/hvac-0/records')['records']),1)

    def test_unique_item_has_only_one_sale_and_packing_slip(self):
        self.reset('reseller');self.wait(self.submit('reseller')['run']['id'])
        extra={'kind':'sale','action':{'buyer':'Demo Buyer','ship_to':'1 Sample Street','sale_ref':'S-1'},'event_id':'sale-1'}
        run=self.wait(self.submit('reseller',**extra)['run']['id'])
        self.assertEqual(run['outputs'][0]['record']['payload']['stock_quantity'],0)
        self.assertEqual(run['outputs'][2]['record']['payload']['status'],'Ready to pack')
        self.assertTrue(self.submit('reseller',**extra)['reused'])
        extra['event_id']='sale-2';extra['action']['sale_ref']='S-2'
        bad=self.wait(self.submit('reseller',**extra)['run']['id'],'needs_attention')
        self.assertIn('already sold',bad['message'])

    def test_capacity_waitlist_and_checkin(self):
        self.reset('events');data=dict(defaults('events'),capacity=1)
        first=self.wait(self.submit('events',data)['run']['id'])
        waitlisted=dict(data,registration_ref='WAIT-1',full_name='Waiting Example')
        second=self.wait(self.submit('events',waitlisted)['run']['id'])
        self.assertEqual(second['outputs'][1]['record']['payload']['status'],'Waitlisted')
        self.assertEqual(second['outputs'][2]['record']['payload']['status'],'Waitlisted')
        check=self.wait(self.submit('events',waitlisted,kind='checkin',event_id='check-wait')['run']['id'],'needs_attention')
        self.assertEqual(check['outputs'],[])
        done=self.wait(self.submit('events',data,kind='checkin',event_id='check-seat')['run']['id'])
        self.assertTrue(all(o['record']['payload']['status']=='Checked in' for o in done['outputs']))

    def test_document_review_and_invoice_matching_block_invalid_input(self):
        self.reset('legal');data=dict(defaults('legal'),other_party='Existing demo client')
        self.request('/api/runs',{'scenario':'legal','data':data},422)
        self.assertEqual(self.request('/api/workplaces/legal-0/records')['records'],[])
        self.wait(self.submit('legal',dict(data,_review_confirmed=True))['run']['id'])
        self.reset('property');self.wait(self.submit('property')['run']['id'])
        action={'invoice_ref':'INV-1','job_reference':'WRONG','invoice_total':180}
        self.request('/api/runs',{'scenario':'property','data':defaults('property'),'kind':'invoice','action':action,'event_id':'I-1'},422)
        action['job_reference']='FIX-016';action['invoice_total']='invalid'
        self.request('/api/runs',{'scenario':'property','data':defaults('property'),'kind':'invoice','action':action,'event_id':'I-2'},422)
        action['invoice_total']=180
        self.wait(self.submit('property',kind='invoice',action=action,event_id='I-3')['run']['id'])

    def test_excel_cleanup_mapping_and_held_rows(self):
        for key,scene in DEFINITIONS.items():
            with self.subTest(scenario=key):
                blob=xlsx_bytes(messy_matrix(scene));source=import_file(blob,key+'.xlsx')
                self.assertEqual(source['header_row'],4);self.assertEqual(len(source['rows']),3)
                self.assertGreater(source['cleanup_count'],2);self.assertTrue(source['rows'][-1]['duplicate'])
                mapping=suggest_mapping(source['columns'],scene['fields'])
                self.assertEqual(set(mapping),{f['key'] for f in scene['fields']})
        source=self.request('/api/sources/upload',{'name':'hvac.xlsx','base64':base64.b64encode(xlsx_bytes(messy_matrix(DEFINITIONS['hvac']))).decode()},201)
        mapped=self.request('/api/mapping',{'scenario':'hvac','source_id':source['id'],'row':0})
        self.assertEqual(mapped['data']['email'],'avery@example.invalid')
        self.assertEqual(mapped['data']['fee'],'95')
        self.reset('hvac');self.wait(self.submit('hvac',mapped['data'],source=mapped['source'])['run']['id'])
        bad=self.request('/api/mapping',{'scenario':'hvac','source_id':source['id'],'row':1})
        self.request('/api/runs',{'scenario':'hvac','data':bad['data']},422)

    @unittest.skipUnless(shutil.which('pdftotext'),'Poppler is not installed')
    def test_real_pdf_import_export_and_excel_export(self):
        scene=DEFINITIONS['legal'];blob=pdf_bytes('Legal intake',[f"{f['label']}: {f['default']}" for f in scene['fields']])
        parsed=import_file(blob,'intake.pdf')
        self.assertEqual(parsed['extraction_tool'],'pdftotext')
        self.assertIn('Casey Example',parsed['extracted_text'])
        self.reset('legal');run=self.wait(self.submit('legal')['run']['id'])
        report=self.request('/api/runs/'+run['id']+'/report.pdf')
        text=subprocess.run(['pdftotext','-','-'],input=report,capture_output=True,check=True).stdout.decode()
        self.assertIn(run['id'],text);self.assertIn('Casey Example',text)
        workbook=self.request('/api/runs/'+run['id']+'/report.xlsx')
        with zipfile.ZipFile(io.BytesIO(workbook)) as z:self.assertIn('xl/worksheets/sheet1.xml',z.namelist())
        bundle=self.request('/api/runs/'+run['id']+'/evidence.zip')
        with zipfile.ZipFile(io.BytesIO(bundle)) as z:self.assertIn('run-and-http-trace.json',z.namelist())

    def test_reset_invalidates_deduplication_but_retains_run_history(self):
        self.reset('sports');first=self.wait(self.submit('sports')['run']['id'])
        self.reset('sports');second=self.wait(self.submit('sports')['run']['id'])
        self.assertNotEqual(first['id'],second['id'])
        self.assertEqual(self.request('/api/runs/'+first['id'])['status'],'archived')
        self.request('/api/runs/'+first['id']+'/resume',{},409)

    def test_intervening_destination_edit_is_not_reported_as_verified(self):
        self.reset('hvac');original=self.engine.api;intervened=[]
        def intercept(method,path,data=None,run_id=None,stage=-1,kind='api'):
            if method=='GET' and stage==2 and kind=='readback' and not intervened:
                intervened.append(True)
                request=self.engine.run(run_id)['steps'][-1]['data']['request']
                request['payload']['fee']=777
                request['operation_id']='independent-user-edit'
                original('POST','/v1/hvac-2/records',request)
            return original(method,path,data,run_id,stage,kind)
        with patch.object(self.engine,'api',side_effect=intercept):
            run=self.wait(self.submit('hvac')['run']['id'],'needs_attention')
        self.assertIn('read-back did not match',run['message'])
        self.assertEqual(len(run['outputs']),2)
        self.assertEqual(run['steps'][-1]['kind'],'readback')

    def test_source_allowlist_and_cross_origin_protection(self):
        self.request('/api/sources/google',{'url':'http://127.0.0.1:8766/private'},422)
        req=urllib.request.Request(self.base+'/api/reset',data=b'{"scenario":"hvac"}',headers={'Content-Type':'application/json','Origin':'https://untrusted.example'})
        with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(req)
        self.assertEqual(error.exception.code,403)
        error.exception.close()
        with self.assertRaises(urllib.error.HTTPError) as error:urllib.request.urlopen(f'http://127.0.0.1:{self.api_server.server_port}/v1/hvac-0/records')
        self.assertEqual(error.exception.code,401)
        error.exception.close()


if __name__=='__main__':unittest.main()
