#!/usr/bin/env python3
# ==============================================================================
# Program: launch.py
# Programmer: Ethan-da-Tech-Wizard
# Last Modified: November 18, 2026
# Purpose: Educational automation and workflow orchestration module for free_intro.
#          Provides structured data generation, asset planning, and contracts.
# ==============================================================================
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

ROOT=Path(__file__).resolve().parents[1]
# Fixed address of the normal demo instance; ready() and the browser target both use it.
URL='http://127.0.0.1:8875'

def ready():
    """Return True when this workspace's normal server is up and answering with the expected config."""
    try:
        # Healthy only if the server answers, uses THIS workspace's runtime/ directory, and exposes
        # all eight scenarios; another program on the same port therefore does not count as ready.
        with urllib.request.urlopen(URL+'/api/config',timeout=2) as response:config=json.load(response)
        return Path(config.get('data_dir','')).resolve()==(ROOT/'runtime').resolve() and len(config.get('scenarios',[]))==8
    except (OSError,ValueError,urllib.error.URLError):return False

def owned_servers():
    """Match only this project's normal instance, never another Python service."""
    matches=[]
    # Scan /proc (Linux only) for python processes; /proc/<pid>/cmdline is NUL-separated.
    for entry in Path('/proc').iterdir():
        if not entry.name.isdigit():continue
        try:
            words=(entry/'cmdline').read_bytes().decode().rstrip('\0').split('\0')
            # Skip anything that is not 'python <script> ...'.
            if len(words)<2 or not Path(words[0]).name.startswith('python'):continue
            cwd=(entry/'cwd').resolve(strict=True)
            script=Path(words[1])
            # Resolve a relative script path against the process's own working directory.
            if not script.is_absolute():script=cwd/script
            if script.resolve()!=(ROOT/'app/server.py').resolve():continue
            # Re-parse the server's arguments exactly as the server would, so a custom port or data dir
            # (i.e. not the normal instance) is rejected below rather than matched by accident.
            options=argparse.ArgumentParser(add_help=False)
            options.add_argument('--port',type=int,default=8875)
            options.add_argument('--workplace-port',type=int,default=8876)
            options.add_argument('--data-dir',default=str(ROOT/'runtime'))
            options.add_argument('--verbose',action='store_true')
            parsed,unknown=options.parse_known_args(words[2:])
            directory=Path(parsed.data_dir)
            if not directory.is_absolute():directory=cwd/directory
            # Only the default ports and this workspace's runtime/ directory count as the normal instance.
            if unknown or parsed.port!=8875 or parsed.workplace_port!=8876 or directory.resolve()!=(ROOT/'runtime').resolve():continue
            matches.append(int(entry.name))
        # Processes can vanish mid-scan; argparse exits via SystemExit on bad args. Ignore both.
        except (OSError,ValueError,SystemExit):continue
    return matches

def stop():
    """Gracefully stop this workspace's normal server. Returns a process exit code (0 ok, 1 failure)."""
    matches=owned_servers()
    if not matches:
        print('No normal Relayworks server from this workspace is running.');return 0
    if len(matches)!=1:
        print('More than one matching server was found; stop each from its own terminal.',file=sys.stderr);return 1
    # SIGINT asks the server to shut down cleanly (no forced kill is ever used).
    pid=matches[0]
    try:os.kill(pid,signal.SIGINT)
    except ProcessLookupError:pass
    # Wait up to ~10 s (100 x 0.1 s) for the process to disappear.
    for _ in range(100):
        if pid not in owned_servers():
            print('Relayworks stopped. Saved records remain in runtime/.');return 0
        time.sleep(.1)
    print('The server is still finishing work. Check again with --status; no forced termination was used.',file=sys.stderr)
    return 1

def main():
    # description reuses the module docstring.
    """Command-line entry point: --status, --stop, or start-if-needed then open the browser. Returns an exit code."""
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-browser',action='store_true',help='Start/check without opening a browser tab.')
    parser.add_argument('--book',choices=['works','business'],help='Open a checklist instead of the overview.')
    operation=parser.add_mutually_exclusive_group()
    operation.add_argument('--status',action='store_true',help='Report whether this workspace is serving the normal address.')
    operation.add_argument('--stop',action='store_true',help='Gracefully stop only this workspace\'s normal server, preserving its records.')
    args=parser.parse_args()
    if args.status:
        print('Relayworks ready: '+URL if ready() else 'Relayworks is not responding at '+URL)
        return 0
    if args.stop:return stop()
    # Not running yet: start app/server.py detached (own session, output to runtime/launcher.log)
    # and poll up to ~10 s (80 x 0.125 s) for it to become ready.
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
        # for/else: runs only if the loop finished without break, i.e. the server never became ready.
        else:
            print('Startup is taking longer than expected. Read runtime/launcher.log.',file=sys.stderr);return 1
    # Pick the page to open: the overview by default, or one of the two books.
    target=URL+({'works':'/THE_WORKS.html','business':'/BUSINESS_PLAYBOOK.html'}.get(args.book,'/'))
    print('Relayworks ready: '+target)
    if not args.no_browser:webbrowser.open(target,new=2)
    return 0

if __name__=='__main__':raise SystemExit(main())
