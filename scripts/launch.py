#!/usr/bin/env python3
# Program: free_intro - launch.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Starts (or reuses) the local demo server for this workspace, opens it in a browser, and can report its status or stop it.
"""Start or open this workspace's demo; no package installation or data reset."""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser

# ---- Setup ----
# Repository root and the fixed local address the demo is served from.
ROOT=Path(__file__).resolve().parents[1]
URL='http://127.0.0.1:8765'

# ---- Status and process helpers ----
def ready():
    """Return True when the server at the normal address is this workspace's own demo (right data folder, eight scenarios)."""
    try:
        with urllib.request.urlopen(URL+'/api/config',timeout=2) as response:config=json.load(response)
        return Path(config.get('data_dir','')).resolve()==(ROOT/'runtime').resolve() and len(config.get('scenarios',[]))==8
    except (OSError,ValueError,urllib.error.URLError):return False

def owned_servers():
    """Match only this project's normal instance, never another Python service."""
    matches=[]
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():continue
        try:
            words=(entry/'cmdline').read_bytes().decode().rstrip('\0').split('\0')
            if len(words)<2 or not Path(words[0]).name.startswith('python'):continue
            cwd=(entry/'cwd').resolve(strict=True)
            script=Path(words[1])
            if not script.is_absolute():script=cwd/script
            if script.resolve()!=(ROOT/'app/server.py').resolve():continue
            options=argparse.ArgumentParser(add_help=False)
            options.add_argument('--port',type=int,default=8765)
            options.add_argument('--workplace-port',type=int,default=8766)
            options.add_argument('--data-dir',default=str(ROOT/'runtime'))
            options.add_argument('--verbose',action='store_true')
            parsed,unknown=options.parse_known_args(words[2:])
            directory=Path(parsed.data_dir)
            if not directory.is_absolute():directory=cwd/directory
            if unknown or parsed.port!=8765 or parsed.workplace_port!=8766 or directory.resolve()!=(ROOT/'runtime').resolve():continue
            matches.append(int(entry.name))
        except (OSError,ValueError,SystemExit):continue
    return matches

def stop():
    """Gracefully stop this workspace's demo server, if exactly one matching process is found.

    Sends an interrupt signal and waits up to ten seconds; it never force-kills. Returns an exit code.
    """
    matches=owned_servers()
    if not matches:
        print('No normal Relayworks server from this workspace is running.');return 0
    if len(matches)!=1:
        print('More than one matching server was found; stop each from its own terminal.',file=sys.stderr);return 1
    pid=matches[0]
    try:os.kill(pid,signal.SIGINT)
    except ProcessLookupError:pass
    for _ in range(100):
        if pid not in owned_servers():
            print('Relayworks stopped. Saved records remain in runtime/.');return 0
        time.sleep(.1)
    print('The server is still finishing work. Check again with --status; no forced termination was used.',file=sys.stderr)
    return 1

def main():
    """Parse options, start the server if needed, wait for it to answer, then open the page.

    Returns a process exit code.
    """
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-browser',action='store_true',help='Start/check without opening a browser tab.')
    parser.add_argument('--book',choices=['works','business'],help='Open a checklist instead of the overview.')
    operation=parser.add_mutually_exclusive_group()
    operation.add_argument('--status',action='store_true',help='Report whether this workspace is serving the normal address.')
    operation.add_argument('--stop',action='store_true',help='Gracefully stop only this workspace\'s normal server, preserving its records.')
    args=parser.parse_args()
    # --status and --stop act on a running server and exit.
    if args.status:
        print('Relayworks ready: '+URL if ready() else 'Relayworks is not responding at '+URL)
        return 0
    if args.stop:return stop()
    # Start the server in its own session, logging to runtime/launcher.log, then wait up to about ten seconds for it.
    if not ready():
        runtime=ROOT/'runtime';runtime.mkdir(exist_ok=True)
        with (runtime/'launcher.log').open('ab') as log:
            process=subprocess.Popen([sys.executable,str(ROOT/'app/server.py')],cwd=ROOT,stdin=subprocess.DEVNULL,stdout=log,stderr=log,start_new_session=True)
        for _ in range(80):
            if ready():break
            if process.poll() is not None:
                print('The demo could not start. Read '+str(runtime/'launcher.log')+' or use the startup chapter in THE_WORKS.html.',file=sys.stderr)
                return 1
            time.sleep(.125)
        else:
            print('Startup is taking longer than expected. Read runtime/launcher.log.',file=sys.stderr);return 1
    # Pick the page to open: the overview, or one of the books.
    target=URL+({'works':'/THE_WORKS.html','business':'/BUSINESS_PLAYBOOK.html'}.get(args.book,'/'))
    print('Relayworks ready: '+target)
    if not args.no_browser:webbrowser.open(target,new=2)
    return 0

# Run only when executed directly.
if __name__=='__main__':raise SystemExit(main())
