#!/usr/bin/env python3
"""Execute local file/tool lessons and retain the exact commands and outcomes."""
from datetime import datetime,timezone
import hashlib,json,os
from pathlib import Path
import shutil,subprocess,sys,tempfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from config import DEFINITIONS
from data_tools import read_xlsx,import_file

out=ROOT/'audit/file-lessons';out.mkdir(parents=True,exist_ok=True)
proof={'started_at':datetime.now(timezone.utc).isoformat(),'steps':[]}
def command(chapter,title,args,env=None,timeout=60):
    run=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,env=env,timeout=timeout)
    result={'chapter':chapter,'title':title,'command':args,'exit_code':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'checked_at':datetime.now(timezone.utc).isoformat()}
    proof['steps'].append(result)
    (out/'commands.json').write_text(json.dumps(proof,indent=2))
    if run.returncode:raise RuntimeError(title+': '+run.stderr)
    print('PASS',title,flush=True)
    return run

command('01','Launcher status identifies the isolated instance',[sys.executable,'scripts/launch.py','--status'])
command('07','Regenerate every CSV, XLSX, PDF and HVAC scan',[sys.executable,'scripts/make_practice_files.py'])
with tempfile.TemporaryDirectory(prefix='relayworks-calc-') as profile:
    for id,s in DEFINITIONS.items():
        p=ROOT/'practice_files'/f'{id}-ugly.xlsx'
        command('07',f'Open {id} workbook in real LibreOffice and convert it to CSV',['libreoffice','-env:UserInstallation='+Path(profile).as_uri(),'--headless','--convert-to','csv','--outdir',str(out),str(p)])
        text=(out/f'{id}-ugly.csv').read_text();assert s['fields'][0]['label'].upper() in text
        command('07',f'Read {id} intake PDF with Poppler',['pdftotext',str(ROOT/'practice_files'/f'{id}-intake.pdf'),str(out/f'{id}-intake.txt')])
        source=import_file(p.read_bytes(),p.name)
        assert source['header_row']==4 and len(source['rows'])==3
        assert source['rows'][2]['duplicate']
        if any(f['type']=='email' or f['key'] in ['slot','event_date','appointment'] for f in s['fields']):assert source['rows'][1]['issues']
        proof['steps'].append({'chapter':'07','title':id+' spreadsheet structure','status':'passed','header_row':4,'rows':[5,7,8],'duplicate_row':8,'review_issues':source['rows'][1]['issues']})
        (out/'commands.json').write_text(json.dumps(proof,indent=2))
command('09','Run Tesseract on the actual supplied PNG',['tesseract',str(ROOT/'practice_files/hvac-scanned-intake.png'),str(out/'scan-text')])
assert 'Avery' in (out/'scan-text.txt').read_text()
board=json.loads((ROOT/'diagrams/showcase.archi.json').read_text());assert len(board['views'])==10
copy=out/'my-client-workflow.archi.json';shutil.copy2(ROOT/'diagrams/showcase.archi.json',copy)
env=dict(os.environ,QT_QPA_PLATFORM='offscreen')
for view in board['views']:
    sample=dict(board,activeView=view['id']);file=out/(view['id']+'.archi.json');file.write_text(json.dumps(sample))
    command('22','Archi opens and renders '+view['title'],['/home/ethan/pg/archi/build/archi','--export-png',str(file),str(out/(view['id']+'.png'))],env=env)
proof['archi_master_sha256']=hashlib.sha256((ROOT/'diagrams/showcase.archi.json').read_bytes()).hexdigest()
proof['desktop_boundary']='Dolphin/Kitty commands and files are checked; physical KRunner keystrokes, file-manager double clicks, trust prompts, and Save As clicks are not claimed as automated desktop actions.'
proof['status']='passed';proof['finished_at']=datetime.now(timezone.utc).isoformat();(out/'commands.json').write_text(json.dumps(proof,indent=2)+'\n')
