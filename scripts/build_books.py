#!/usr/bin/env python3
"""Build the two offline checklist books from Markdown and actual app contracts."""
import hashlib
import html
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'app'))
from config import DEFINITIONS

BOOKS=[('THE_WORKS','works','01','The Works','The complete operator’s book','Learn every screen, every handoff, and every recovery.'),
       ('BUSINESS_PLAYBOOK','business','02','The Business Owner Playbook','The conversation and demonstration book','Ask better questions. Show the proof. Define useful work.')]

def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','| '+' | '.join(['---']*len(headers))+' |']+['| '+' | '.join(str(c).replace('|',' / ').replace('\n',' ') for c in row)+' |' for row in rows])

def field_table(s):
    return table(['Form label','Exact practice value','Requirement'],[[f['label'],'`'+str(f['default'])+'`','Required' if f['required'] else 'Optional'] for f in s['fields']])

def expand(source):
    stations=table(['Workflow','Fictional business','Three independent apps'],[[s['short'],s['company'],' → '.join(t['name'] for t in s['targets'])] for s in DEFINITIONS.values()])
    source=source.replace('{{STATIONS}}',stations)
    source=re.sub(r'\{\{FIELDS:(\w+)\}\}',lambda m:field_table(DEFINITIONS[m[1]]),source)
    reference=[]
    for s in DEFINITIONS.values():
        reference+=['### '+s['short']+' · '+s['company'],field_table(s)]
        fields={f['key']:f for f in s['fields']}
        for i,t in enumerate(s['targets']):
            reference+=['#### '+t['name']+' · '+str(len(s['stage_fields'][i]))+' manual fields',
                'Open **Do it manually → Open '+t['name']+'**. Enter the following fields, then click **Save to '+t['name']+'**.',
                table(['Form label','Value to enter','Destination API field'],[[fields[k]['label'],'`'+str(fields[k]['default'])+'`','`'+t['mapping'][k]+'`'] for k in s['stage_fields'][i]])]
    return source.replace('{{REFERENCE}}','\n\n'.join(reference))

def inline(value):
    tokens=[]
    def save(text):
        tokens.append(text);return '\x00'+str(len(tokens)-1)+'\x00'
    value=re.sub(r'`([^`]+)`',lambda m:save('<code>'+html.escape(m[1])+'</code>'),value)
    value=re.sub(r'\[([^\]]+)\]\(([^\s)]+)\)',lambda m:save('<a href="'+html.escape(m[2],quote=True)+'"'+(' target="_blank" rel="noopener"' if m[2].startswith('http') else '')+'>'+html.escape(m[1])+'</a>'),value)
    value=html.escape(value)
    value=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',value)
    return re.sub(r'\x00(\d+)\x00',lambda m:tokens[int(m[1])],value)

def render(source,chapter):
    lines=source.strip().splitlines();out=[];i=0;task_count=0
    while i<len(lines):
        line=lines[i].strip()
        if not line:i+=1;continue
        if line.startswith('```'):
            code=[];i+=1
            while i<len(lines) and not lines[i].startswith('```'):code.append(lines[i]);i+=1
            out.append('<pre><code>'+html.escape('\n'.join(code))+'</code></pre>');i+=1;continue
        if line.startswith(':::notes '):
            key,label=line[9:].split('|',1)
            out.append(f'<div class="notes"><label for="note-{html.escape(key)}"><strong>Your notes</strong><span>{inline(label)}</span></label><textarea id="note-{html.escape(key)}" data-note="{html.escape(key)}" rows="6" placeholder="Write here. Saved in this browser; use Export progress for a backup."></textarea><div class="print-note" data-print-note="{html.escape(key)}">________________________________________________________________________<br><br>________________________________________________________________________<br><br>________________________________________________________________________</div></div>');i+=1;continue
        image=re.fullmatch(r'!\[([^\]]+)\]\(([^)]+)\)',line)
        if image:
            path=image[2].removeprefix('../')
            out.append('<figure><a href="'+html.escape(path)+'" target="_blank" rel="noopener"><img src="'+html.escape(path)+'" alt="'+html.escape(image[1])+'" loading="lazy"></a><figcaption>'+inline(image[1])+'</figcaption></figure>');i+=1;continue
        heading=re.match(r'^(#{1,4}) (.+)',line)
        if heading:
            level=len(heading[1]);out.append(f'<h{level}>'+inline(heading[2])+f'</h{level}>');i+=1;continue
        if line.startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].strip().startswith('|'):
                cells=[x.strip() for x in lines[i].strip().strip('|').split('|')]
                if not all(re.fullmatch(r':?-+:?',c) for c in cells):rows.append(cells)
                i+=1
            out.append('<div class="table-wrap" tabindex="0" role="region" aria-label="Reference table"><table><thead><tr>'+''.join('<th scope="col">'+inline(c)+'</th>' for c in rows[0])+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+inline(c)+'</td>' for c in row)+'</tr>' for row in rows[1:])+'</tbody></table></div>');continue
        if line.startswith('- '):
            out.append('<ul class="checklist">')
            while i<len(lines) and lines[i].strip().startswith('- '):
                item=lines[i].strip()[2:];task=re.match(r'\[([ x])\] (.+)',item)
                if task:
                    key=chapter+'-'+hashlib.sha256(task[2].encode()).hexdigest()[:12]
                    out.append('<li class="task"><label><input type="checkbox" data-task="'+key+'"'+(' checked' if task[1]=='x' else '')+'><span>'+inline(task[2])+'</span></label></li>');task_count+=1
                else:out.append('<li>'+inline(item)+'</li>')
                i+=1
            out.append('</ul>');continue
        paragraph=[line];i+=1
        while i<len(lines) and lines[i].strip() and not lines[i].startswith(('#','- ','|','```',':::notes ','![')):
            paragraph.append(lines[i].strip());i+=1
        out.append('<p>'+inline(' '.join(paragraph))+'</p>')
    return '\n'.join(out),task_count

def build(meta):
    stem,book_id,volume,title,subtitle,tagline=meta
    source=expand((ROOT/'docs'/f'{stem}.md').read_text())
    if '{{' in source:raise ValueError('Unexpanded book marker')
    parts=re.split(r'^## (\d{2}\. .+)$',source,flags=re.M)
    intro=parts[0].split('\n',1)[1]
    chapters=[];total=0
    for n in range(1,len(parts),2):
        label=parts[n];chapter='chapter-'+label[:2];content,count=render(parts[n+1],chapter)
        total+=count;chapters.append({'id':chapter,'title':label,'count':count,'body':content})
    contents=''.join(f'<a href="#{c["id"]}" data-chapter-link="{c["id"]}"><span>{html.escape(c["title"])}</span><small data-chapter-progress="{c["id"]}">0 / {c["count"]}</small></a>' for c in chapters)
    body=''.join(f'<section class="chapter" id="{c["id"]}" data-count="{c["count"]}"><div class="chapter-meta">CHAPTER {c["title"][:2]} · {c["count"]} CHECKPOINTS</div><h2>{html.escape(c["title"][4:])}</h2>{c["body"]}</section>' for c in chapters)
    other='BUSINESS_PLAYBOOK' if book_id=='works' else 'THE_WORKS'
    css=(ROOT/'web/books.css').read_text()
    document=f'''<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title} · Relayworks</title><style>{css}</style><script src="web/books.js" defer></script></head>
<body data-book="{book_id}"><a class="skip" href="#reading">Skip to reading</a>
<aside class="contents" id="contents"><a class="brand" href="START_HERE.html">↗ relayworks <small>FIELD LIBRARY</small></a><div class="volume">BOOK {volume} / 02</div><h2>{title}</h2><p class="muted">{len(chapters)} chapters · {total} checkpoints</p><div class="progress-track"><div id="progress-bar"></div></div><p id="progress-label" aria-live="polite">0 of {total} complete</p><h3>Contents</h3><nav aria-label="Table of contents">{contents}</nav><div class="library-links"><a href="{other}.html">Open the other book ↗</a><a href="START_HERE.html">Library & startup</a><a href="books/{stem}.pdf" target="_blank">Blank PDF edition ↗</a></div></aside>
<div class="reader"><header class="reader-toolbar"><button id="contents-button" aria-controls="contents" aria-expanded="false">Contents</button><label class="search"><span class="sr-only">Search this book</span><input id="book-search" type="search" placeholder="Search this book" autocomplete="off"></label><button id="mode-button">Read whole book</button><button id="print-button">Print / save PDF</button><a class="button open-demo" href="http://127.0.0.1:8765/" target="_blank" rel="noopener">Open demo ↗</a><div class="progress-actions"><button id="export-button">Export progress</button><button id="import-button">Import progress</button><input id="import-file" type="file" accept=".json,application/json" hidden></div></header>
<div id="reader-status" class="reader-status" role="status" aria-live="polite">Checkmarks and notes stay in this browser. Export them for a backup.</div>
<main id="reading"><div class="cover" id="book-cover"><div class="eyebrow">RELAYWORKS / BOOK {volume}</div><p class="subtitle">{subtitle}</p><h1>{title}</h1><p class="tagline">{tagline}</p>{render(intro,'intro')[0]}<p class="edition">Prepared for this workspace · September 24, 2026 · All practice businesses and people are fictional.</p></div>
<div class="print-toc"><h2>Contents</h2><ol>{''.join('<li>'+html.escape(c['title'])+'</li>' for c in chapters)}</ol></div><p id="search-result" hidden></p><p id="no-results" hidden>No chapters match. Clear the search or try another word.</p>{body}
<nav class="chapter-pager" aria-label="Chapter navigation"><button id="previous-button">Previous chapter</button><span id="chapter-position"></span><button id="next-button">Next chapter</button></nav>
<noscript><p>JavaScript is disabled. The complete book is readable; saved progress, search, and chapter controls require JavaScript.</p></noscript></main></div></body></html>'''
    (ROOT/f'{stem}.html').write_text(document)
    (ROOT/'books'/f'{stem}.md').write_text(source)
    return {'id':book_id,'title':title,'file':stem+'.html','chapters':len(chapters),'checkpoints':total,'words':len(source.split())}

def main():
    (ROOT/'books').mkdir(exist_ok=True)
    manifest=[build(meta) for meta in BOOKS]
    (ROOT/'books/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    css=(ROOT/'web/books.css').read_text()
    cards=''.join(f'<article class="book-card"><div class="eyebrow">BOOK 0{i+1}</div><h2>{m["title"]}</h2><p>{BOOKS[i][5]}</p><p class="muted">{m["chapters"]} chapters · {m["checkpoints"]} checkpoints</p><a class="button primary" href="{m["file"]}">Open this book →</a><a class="pdf-link" href="books/{BOOKS[i][0]}.pdf" target="_blank">Printable PDF ↗</a></article>' for i,m in enumerate(manifest))
    (ROOT/'START_HERE.html').write_text(f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Start here · Relayworks</title><style>{css}</style></head><body class="landing"><main><a class="brand" href="START_HERE.html">↗ relayworks <small>FIELD LIBRARY</small></a><div class="eyebrow">YOUR TWO COMPLETE CHECKLIST BOOKS</div><h1>Learn the work.<br>Then show what it can do.</h1><p class="tagline">Start at your desktop. Practice every workflow. Walk into the conversation with the evidence and the words to explain it.</p><div class="book-grid">{cards}</div><section class="startup-card"><h2>First time here?</h2><ol><li>Open <strong>The Works</strong> above. Read chapter <strong>01. Open the books and start the demo</strong> for the exact file-manager and terminal instructions.</li><li>In Dolphin, open <code>/home/ethan/pg/free_intro</code> and double-click <strong>START_RELAYWORKS.desktop</strong>. If prompted, follow the trust or terminal instructions in chapter 01.</li><li>Or open Kitty and run these two lines:<pre><code>cd /home/ethan/pg/free_intro\npython3 scripts/launch.py</code></pre></li><li>When the service is ready, <a href="http://127.0.0.1:8765/" target="_blank" rel="noopener">open the demo ↗</a>. Keep your book in a separate tab.</li></ol><p>The books work as local files before the service starts. The demo requires the local server. Each book has a table of contents, search, saved checkmarks, notes, progress export/import, and print controls.</p><p>Practice files are ready in <code>practice_files/</code>. Blank PDF and complete Markdown editions are in <code>books/</code>. Browser notes stay on this computer; no account or paid service is required.</p></section><p class="edition">Built for /home/ethan/pg/free_intro · September 24, 2026</p></main></body></html>''')
    print(json.dumps(manifest,indent=2))

if __name__=='__main__':main()
