# ==============================================================================
# Program: test_operations.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Educational automation and workflow orchestration module for free_intro.
#          Provides structured data generation, asset planning, and contracts.
# ==============================================================================
"""Real process restart, scan OCR, and office/calendar interoperability."""
import base64
from datetime import datetime
import json
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

# Make the app package importable without installing it.
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from config import DEFINITIONS,defaults
from data_tools import pdf_bytes,xlsx_bytes,import_file,messy_matrix


class Operations(unittest.TestCase):
    """Tests that use real processes and real local tools rather than in-process fakes."""
    def test_server_process_restart_retains_records_and_resumes_failed_job(self):
        """Kill and restart the server; stored records and the failed run must survive and resume."""
        with tempfile.TemporaryDirectory(prefix='relay-restart-') as directory:
            # Helpers: free-port finder, JSON request, start/stop server subprocess, poll a run until it reaches a state.
            def port():
                with socket.socket() as sock:sock.bind(('127.0.0.1',0));return sock.getsockname()[1]
            portal_port,api_port=port(),port();base=f'http://127.0.0.1:{portal_port}'
            def request(path,body=None):
                req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
                with urllib.request.urlopen(req,timeout=3) as response:
                    blob=response.read();return json.loads(blob) if 'application/json' in response.headers['Content-Type'] else blob
            def start():
                proc=subprocess.Popen([sys.executable,str(ROOT/'app/server.py'),'--port',str(portal_port),'--workplace-port',str(api_port),'--data-dir',directory],stdout=subprocess.DEVNULL,stderr=subprocess.PIPE)
                for _ in range(60):
                    try:request('/api/config');return proc
                    except (urllib.error.URLError,ConnectionError):time.sleep(.05)
                proc.kill();out=proc.communicate()[1];self.fail(out.decode())
            def stop(proc):
                proc.send_signal(signal.SIGINT);_,err=proc.communicate(timeout=10)
                self.assertEqual(proc.returncode,0,err.decode())
            def wait(run_id,state):
                for _ in range(100):
                    result=request('/api/runs/'+run_id)
                    if result['status']==state:return result
                    time.sleep(.025)
                self.fail(result)
            proc=start()
            try:
                request('/api/workplaces/hvac-2/settings',{'online':False})
                # Take the second destination offline so the run stops half-way with its first records saved.
                rid=request('/api/runs',{'scenario':'hvac','data':defaults('hvac')})['run']['id']
                # Restart the server process on the same data dir: the saved run and record IDs must survive.
                before=wait(rid,'needs_attention');ids=[o['record']['id'] for o in before['outputs']]
                self.assertEqual(len(ids),2);stop(proc);proc=start()
                after=request('/api/runs/'+rid);self.assertEqual([o['record']['id'] for o in after['outputs']],ids)
                # Bring the destination back and resume; the first two records must be reused (same IDs), not rewritten.
                request('/api/workplaces/hvac-2/settings',{'online':True});request('/api/runs/'+rid+'/resume',{})
                done=wait(rid,'complete');self.assertEqual([o['record']['id'] for o in done['outputs'][:2]],ids)
                self.assertEqual(done['outputs'][0]['record']['revision'],1)
                calendar=request('/api/runs/'+rid+'/calendar.ics').decode()
                self.assertIn('BEGIN:VCALENDAR',calendar);self.assertIn('DTSTART:20261006T170000Z',calendar)
                # RFC 5545 limits content lines to 75 octets.
                self.assertTrue(all(len(line.encode())<=75 for line in calendar.splitlines()))
                # Recordings are operational with the network unused and keep their original timestamp.
                for provider in ['google','openf1']:
                    snapshot=ROOT/'fixtures/public'/f'{provider}.json'
                    if snapshot.exists():
                        replay=request('/api/sources/recorded-'+provider,{})
                        self.assertTrue(replay['kind'].startswith('recorded '));self.assertIn('replayed_at',replay)
                        self.assertEqual(replay['fetched_at'],json.loads(snapshot.read_text())['fetched_at'])
            # Always stop a server we started, even when an assertion failed.
            finally:
                if proc.poll() is None:stop(proc)

    @unittest.skipUnless(shutil.which('pdftoppm') and shutil.which('tesseract'),'Local scan tools are not installed')
    def test_scan_ocr_reads_real_rasterized_intake(self):
        """OCR a rasterised intake PDF (skipped without pdftoppm and tesseract)."""
        with tempfile.TemporaryDirectory(prefix='relay-scan-') as directory:
            # Round trip: generated PDF -> rasterised PNG -> Tesseract OCR; the text and column names must come back.
            root=Path(directory);scene=DEFINITIONS['hvac']
            source=root/'intake.pdf';source.write_bytes(pdf_bytes('Intake',[f"{f['label']}: {f['default']}" for f in scene['fields']]))
            subprocess.run(['pdftoppm','-singlefile','-r','160','-png',str(source),str(root/'scan')],capture_output=True,check=True,timeout=20)
            result=import_file((root/'scan.png').read_bytes(),'scanned-intake.png')
            self.assertEqual(result['extraction_tool'],'Tesseract OCR');self.assertIn('Avery',result['extracted_text'])
            self.assertIn('Customer reference',result['columns'])

    @unittest.skipUnless(shutil.which('libreoffice'),'LibreOffice is not installed')
    def test_exported_workbook_opens_in_actual_libreoffice(self):
        """The exported XLSX must open in headless LibreOffice (skipped when it is not installed)."""
        with tempfile.TemporaryDirectory(prefix='relay-office-') as directory:
            # Convert our hand-built XLSX to CSV with real LibreOffice; success proves the file is a valid workbook
            # (the converter upper-cases the text, hence the capitals below).
            root=Path(directory);source=root/'messy.xlsx';source.write_bytes(xlsx_bytes(messy_matrix(DEFINITIONS['hvac'])))
            process=subprocess.run(['libreoffice','-env:UserInstallation='+(root/'profile').as_uri(),'--headless','--convert-to','csv','--outdir',str(root),str(source)],capture_output=True,timeout=40)
            self.assertEqual(process.returncode,0,process.stderr.decode())
            self.assertTrue((root/'messy.csv').exists(),process.stdout.decode())
            text=(root/'messy.csv').read_text();self.assertIn('AVERY@EXAMPLE.INVALID',text)
            self.assertIn('CUSTOMER REFERENCE',text)


if __name__=='__main__':unittest.main()
