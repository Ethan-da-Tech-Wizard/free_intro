#!/usr/bin/env python3
# Program: free_intro - rehearse_lifecycle.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Rehearses the full life cycle for real: launch, stop, backup, rename, restore and restart, plus a second instance on alternate ports, checking records are preserved.

"""Execute the book's launch, stop, backup, rename, extract, and restart route."""
from datetime import datetime,timezone
import hashlib,importlib.util,json,os
from pathlib import Path
import signal,socket,subprocess,sys,time,urllib.request,zipfile

# Project root, normal address and evidence folder.
ROOT=Path(__file__).resolve().parents[1];BASE='http://127.0.0.1:8875'
OUT=ROOT/'audit/lifecycle';OUT.mkdir(parents=True,exist_ok=True)
# Running record of every step, rewritten after each command.
proof={'started_at':datetime.now(timezone.utc).isoformat(),'steps':[]}
def get(route,base=BASE):
    """GET a JSON route from the demo server."""
    with urllib.request.urlopen(base+route,timeout=5) as r:return json.load(r)
def command(title,args,expected=0):
    """Run a command, record its output, and assert the expected exit code."""
    p=subprocess.run(args,cwd=ROOT,capture_output=True,text=True,timeout=20)
    proof['steps'].append({'title':title,'command':args,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'checked_at':datetime.now(timezone.utc).isoformat()})
    (OUT/'proof.json').write_text(json.dumps(proof,indent=2))
    assert p.returncode==expected,(title,p.stdout,p.stderr)
    print('PASS',title,flush=True)
def snapshot():
    """Capture the dashboard and every destination app's records for before/after comparison."""
    cfg=get('/api/config')
    return {'dashboard':get('/api/dashboard'),'records':{t['id']:get('/api/workplaces/'+t['id']+'/records')['records'] for s in cfg['scenarios'] for t in s['targets']}}
def wait(base=BASE):
    """Poll until the server answers or fail after about five seconds."""
    for _ in range(100):
        try:get('/api/config',base);return
        except OSError:time.sleep(.05)
    raise RuntimeError('Server did not start')
# Map each database file in a folder to its SHA-256 hash.
def signatures(directory):return {str(p.relative_to(directory)):hashlib.sha256(p.read_bytes()).hexdigest() for p in directory.rglob('*.sqlite3')}

# Precondition: no schedule is enabled and no run is active, so the state is stable.
assert not get('/api/schedules')['enabled']
before=snapshot();assert not any(r['status'] in ['queued','running'] for r in before['dashboard']['runs'])
(OUT/'before.json').write_text(json.dumps(before,indent=2))
# Launcher checks: status, reuse of a running copy, a clash on the busy port, then a graceful stop.
command('Status identifies the copy',[sys.executable,'scripts/launch.py','--status'])
command('Launch reuses an already-running copy',[sys.executable,'scripts/launch.py','--no-browser'])
command('Launching another direct listener visibly reports address already in use',[sys.executable,'app/server.py'],1)
command('Stop only this copy; retain saved state',[sys.executable,'scripts/launch.py','--stop'])
try:get('/api/config');raise AssertionError('The server should be stopped')
except OSError:pass
command('Stopped status is visible',[sys.executable,'scripts/launch.py','--status'])
assert (ROOT/'THE_WORKS.html').is_file() and (ROOT/'BUSINESS_PLAYBOOK.html').is_file()
# Foreground start: records must be unchanged after a stop and start, and SIGINT must exit cleanly.
log=(OUT/'foreground-server.log').open('wb')
foreground=subprocess.Popen([sys.executable,'app/server.py'],cwd=ROOT,stdout=log,stderr=log)
try:wait();assert snapshot()['records']==before['records']
finally:foreground.send_signal(signal.SIGINT);foreground.wait(timeout=15);log.close()
assert foreground.returncode==0
proof['steps'].append({'title':'Direct foreground server started, retained records, and stopped with SIGINT (the signal sent by Ctrl+C)','command':[sys.executable,'app/server.py'],'exit_code':0,'log':'audit/lifecycle/foreground-server.log'})
# Backup and restore: refuse to overwrite an earlier exercise, zip the stopped runtime, move it aside, extract the zip and require identical database hashes.
backup=ROOT/'backups/relayworks-practice-001.zip';previous=ROOT/'runtime-before-restore-001'
assert not backup.exists() and not previous.exists(),'Refusing to overwrite a previous backup exercise.'
command('Create backups directory',['mkdir','-p','backups'])
hashes=signatures(ROOT/'runtime');assert len(hashes)==25
command('Back up stopped runtime',[sys.executable,'-m','zipfile','-c','backups/relayworks-practice-001.zip','runtime'])
with zipfile.ZipFile(backup) as z:assert sum(name.endswith('.sqlite3') for name in z.namelist())==25
(ROOT/'runtime').rename(previous)
proof['steps'].append({'title':'Rename runtime to preserve pre-restore state','from':'runtime','to':'runtime-before-restore-001','method':'filesystem rename; equivalent result to Dolphin F2, not a claim of a GUI click'})
command('Restore the backup made in this exercise',[sys.executable,'-m','zipfile','-e','backups/relayworks-practice-001.zip','.'])
assert signatures(ROOT/'runtime')==hashes
command('Restart restored copy',[sys.executable,'scripts/launch.py','--no-browser'])
# After the restart the records, metrics and run statuses must equal the earlier snapshot.
after=snapshot();assert before['records']==after['records'];assert before['dashboard']['metrics']==after['dashboard']['metrics']
assert [(r['id'],r['status']) for r in before['dashboard']['runs']]==[(r['id'],r['status']) for r in after['dashboard']['runs']]
(OUT/'after.json').write_text(json.dumps(after,indent=2))
# The documented alternate ports use a new directory and never the normal runtime.
# Alternate instance: confirm the ports are free, then run a copy with its own data folder.
for p in [8865,8866]:
    with socket.socket() as sock:sock.bind(('127.0.0.1',p))
log=(OUT/'alternate-server.log').open('wb');alternate=ROOT/'audit/alternate-runtime'
assert not alternate.exists()
args=[sys.executable,'app/server.py','--port','8865','--workplace-port','8866','--data-dir',str(alternate)]
proc=subprocess.Popen(args,cwd=ROOT,stdout=log,stderr=log)
try:wait('http://127.0.0.1:8865');assert Path(get('/api/config','http://127.0.0.1:8865')['data_dir'])==alternate
finally:proc.send_signal(signal.SIGINT);proc.wait(timeout=15);log.close()
assert proc.returncode==0
proof.update(status='passed',finished_at=datetime.now(timezone.utc).isoformat(),database_files_verified=25,byte_identical_restoration=True,saved_records_and_run_ids_preserved=True,records=sum(len(v) for v in after['records'].values()),schedule_enabled=get('/api/schedules')['enabled'])
proof['steps'].append({'title':'Alternate instance on 8865/8866 with separate data; stopped after checking','command':args,'exit_code':0})
(OUT/'proof.json').write_text(json.dumps(proof,indent=2)+'\n')
print('PASS backup/restore: all 25 database files match; normal records and run IDs retained',flush=True)
