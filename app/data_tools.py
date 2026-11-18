# Program: free_intro - data_tools.py
# Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
# Last Modified: 2026-11-18
# Purpose: Reads, cleans, and maps spreadsheet/document/public-API data into rows, and writes simple XLSX and PDF files, using only the standard library.
"""Local document tools, spreadsheet cleanup, and read-only public connectors."""
import csv
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import hashlib
import html
import io
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import textwrap
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile

# ---- Constants ----
# Public example Google Sheet offered as a ready-made import source.
SAMPLE_SHEET = 'https://docs.google.com/spreadsheets/d/1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgvE2upms/edit#gid=0'
# XML namespace used by the spreadsheet files inside an .xlsx archive.
NS = {'x':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
# Alternate spellings of column headings, keyed by the canonical field name.
# Used to guess which source column holds which field.
ALIASES = {
    'full_name':['full name','name','client name','customer name','student name','attendee','patient name','name of customer'],
    'email':['email','e mail','email address','contact email'],
    'phone':['phone','telephone','mobile','contact phone','tel'],
    'street':['street','address','street address','service address','mailing address'],
    'city':['city','town'], 'region':['region','state','province'],
    'postal_code':['zip','zip code','postal code','postcode'],
    'customer_ref':['customer ref','cust','customer id','cust id','customer reference'],
    'job_ref':['job ref','job','job id','work order','job reference'],
    'registration_ref':['registration ref','registration id','registration reference','reg id'],
    'fee':['fee','diagnostic fee','amount','charge','diagnostic fee usd'],
    'quantity':['qty','quantity','count','counted quantity','received qty'],
    'unit_cost':['unit cost','cost','unit cost usd'],
    'sku':['sku','item code','item sku','internal sku'],
    'slot':['slot','visit slot','appointment slot','scheduled','date time'],
    'session':['session','class','major','workshop'],
    'issue':['issue','problem','request','reported issue'],
    'event_date':['event date','date'],
}


def now():
    """Return the current UTC time as an ISO-8601 string with millisecond precision."""
    return datetime.now(timezone.utc).isoformat(timespec='milliseconds')


def normalized_key(value):
    """Reduce a heading to lowercase words separated by single spaces, so headings compare loosely."""
    return re.sub(r'[^a-z0-9]+',' ',str(value).lower()).strip()


def suggest_mapping(columns, fields):
    """Guess which source column feeds each field.

    columns are the source headings and fields the scenario field list. Returns
    {field key: column heading}; fields with no matching column are left out.
    """
    output = {}
    for f in fields:
        # Names a column may use: the field key, its label, or any known alias.
        names = {normalized_key(f['key']), normalized_key(f['label']), *ALIASES.get(f['key'], [])}
        for col in columns:
            if normalized_key(col) in names:
                output[f['key']] = col
                break
    return output


def cleanup_cell(value, column):
    """Tidy one cell and report what was changed and what needs a human look.

    Returns (clean value, list of change notes, list of issues). Rules depend on the
    column heading: email, phone, money amount, or date.
    """
    raw = str(value or '')
    # Collapse runs of whitespace (including non-breaking spaces) to single spaces.
    clean = re.sub(r'\s+', ' ', raw.replace('\xa0',' ')).strip()
    changes, issues = [], []
    key = normalized_key(column)
    if clean != raw:
        changes.append('Whitespace normalized')
    # Email columns: lower-case, strip spaces around the @, and flag anything that is not shaped like an address.
    if key in sum((ALIASES[k] for k in ['email']), []):
        lowered = clean.lower().replace(' @','@').replace('@ ','@')
        if lowered != clean: changes.append('Email normalized')
        clean = lowered
        if clean and not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+',clean):
            issues.append('Email needs correction')
    # Phone columns: 10 digits or 11 starting with 1 become +1 numbers; others are flagged for review.
    if key in ALIASES['phone'] and clean:
        digits = re.sub(r'\D','',clean)
        if len(digits)==10:
            clean = '+1'+digits
        elif len(digits)==11 and digits.startswith('1'):
            clean = '+'+digits
        elif not clean.startswith('+'):
            issues.append('Phone country/format needs review')
        if clean != raw.strip(): changes.append('Phone formatted')
    # Money columns: remove USD, $ and commas, then require a finite number.
    money_words = {'fee','amount','charge','price','cost','total','estimate'}
    if set(key.split()) & money_words and clean:
        candidate = re.sub(r'(?i)\bUSD\b|\$|,','',clean).strip()
        try:
            amount = Decimal(candidate)
            if not amount.is_finite(): raise InvalidOperation
            clean = str(amount)
            if clean != raw.strip(): changes.append('Currency parsed')
        except InvalidOperation:
            issues.append('Amount is not a number')
    # Dates written with slashes are ambiguous (day/month vs month/day), so ask for ISO format.
    if 'date' in key or key in ALIASES['slot']:
        if re.fullmatch(r'\d{1,2}/\d{1,2}/\d{2,4}', clean):
            issues.append('Slash date is ambiguous; choose an ISO date')
    return clean, changes, issues


def read_xlsx(blob):
    """Read the first worksheet of an .xlsx file (given as bytes) into a list of rows of text.

    Guards: the unpacked size is capped at 25 MB, at most 1001 rows and 80 columns
    are read, and formulas with no cached result are marked instead of evaluated.
    """
    with zipfile.ZipFile(io.BytesIO(blob)) as archive:
        if sum(i.file_size for i in archive.infolist()) > 25_000_000:
            raise ValueError('Workbook expands beyond the 25 MB demo limit.')
        # Text cells point into a shared-strings table; load it first.
        shared=[]
        if 'xl/sharedStrings.xml' in archive.namelist():
            root=ET.fromstring(archive.read('xl/sharedStrings.xml'))
            shared=[''.join(n.itertext()) for n in root.findall('x:si',NS)]
        candidates=sorted(n for n in archive.namelist() if re.fullmatch(r'xl/worksheets/sheet\d+\.xml',n))
        if not candidates: raise ValueError('No worksheet found.')
        root=ET.fromstring(archive.read(candidates[0]))
        rows=[]
        for row in root.findall('x:sheetData/x:row',NS)[:1001]:
            values=[]
            for c in row.findall('x:c',NS):
                # Convert the column letters of the cell address (A, B, ..., AA) to a number.
                letters=re.match(r'[A-Z]+',c.get('r','A1')).group()
                index=0
                for letter in letters: index=index*26+ord(letter)-64
                if index>80: continue
                while len(values)<index: values.append('')
                value=c.find('x:v',NS)
                if c.get('t')=='s':
                    text=shared[int(value.text)] if value is not None else ''
                elif c.get('t')=='inlineStr':
                    text=''.join(c.find('x:is',NS).itertext())
                else:
                    text=value.text if value is not None else ''
                    if c.find('x:f',NS) is not None and value is None:
                        text='[Formula has no cached result]'
                values[index-1]=text
            rows.append(values)
        return rows


def read_csv(blob):
    """Read delimited text (bytes) into a list of rows, guessing the delimiter and encoding.

    Tries UTF-8 (with optional BOM) and falls back to Windows-1252. Returns at most 1001 rows.
    """
    try: text=blob.decode('utf-8-sig')
    except UnicodeDecodeError: text=blob.decode('cp1252')
    try: dialect=csv.Sniffer().sniff(text[:8000], delimiters=',;\t|')
    except csv.Error: dialect=csv.excel
    rows=list(csv.reader(io.StringIO(text),dialect))
    # Banner rows can defeat Sniffer; choose the delimiter yielding the widest header.
    if max((len(r) for r in rows),default=0)<2:
        options=[list(csv.reader(io.StringIO(text),delimiter=d)) for d in [';', '\t', '|', ',']]
        rows=max(options,key=lambda rs:max((len(r) for r in rs),default=0))
    return rows[:1001]


def normalize_table(matrix, name, source_kind, header_index=None):
    """Turn a raw grid of cells into the cleaned table structure the app works with.

    Finds the header row (unless header_index is given), makes column names unique,
    cleans every cell, and flags duplicate and problem rows. The result is a dict with
    columns, rows (raw, cleaned, changes, issues), and summary counts.
    """
    if not matrix: raise ValueError('The source is empty.')
    known={v for values in ALIASES.values() for v in values}
    def score(row):
        """Rate how header-like a row is: known headings score high, numeric cells score negative."""
        values=[normalized_key(v) for v in row if str(v).strip()]
        return sum(4 if v in known else 1 for v in values) - sum(v.replace(' ','').isdigit() for v in values)*2
    header_index=max(range(min(len(matrix),15)),key=lambda i:score(matrix[i])) if header_index is None else int(header_index)
    if header_index<0 or header_index>=len(matrix): raise ValueError('Invalid header row.')
    columns=[]
    for i,c in enumerate(matrix[header_index]):
        col=re.sub(r'\s+',' ',str(c)).strip() or f'Column {i+1}'
        if col in columns: col += f' ({i+1})'
        columns.append(col)
    if len(columns)>80: raise ValueError('Use a worksheet with at most 80 columns.')
    rows=[]; seen=set(); changes_total=0; blanks=0
    for index, row in enumerate(matrix[header_index+1:],header_index+2):
        if not any(str(c).strip() for c in row): blanks+=1; continue
        raw={col:str(row[i] if i<len(row) else '') for i,col in enumerate(columns)}
        cleaned={}; changes=[]; issues=[]
        for col,value in raw.items():
            clean, fix, problem=cleanup_cell(value,col)
            cleaned[col]=clean
            changes.extend(f'{col}: {f}' for f in fix)
            issues.extend(f'{col}: {p}' for p in problem)
        # Hash the cleaned values so identical rows can be recognised as duplicates.
        digest=hashlib.sha256(json.dumps(cleaned,sort_keys=True).encode()).hexdigest()
        duplicate=digest in seen
        if duplicate: issues.append('Duplicate of an earlier normalized row')
        seen.add(digest); changes_total+=len(changes)
        rows.append({'row_number':index,'raw':raw,'values':cleaned,'changes':changes,'issues':issues,'duplicate':duplicate})
    return {'name':name,'kind':source_kind,'fetched_at':now(),'columns':columns,'rows':rows,
            'header_row':header_index+1,'skipped_title_rows':header_index,'blank_rows':blanks,
            'cleanup_count':changes_total,'review_count':sum(bool(r['issues']) for r in rows),
            'raw_preview':matrix[:12]}


def extract_document(blob, filename):
    """Pull "Label: value" pairs out of a PDF or image and return them as a one-row table.

    Uses pdftotext for text PDFs and Tesseract OCR for scans and images; both are
    external programs that must be installed. Work happens in a temporary directory.
    """
    suffix=Path(filename).suffix.lower()
    with tempfile.TemporaryDirectory(prefix='relay-import-') as tmp:
        path=Path(tmp)/('source'+suffix); path.write_bytes(blob)
        if suffix=='.pdf':
            if not shutil.which('pdftotext'): raise ValueError('Install Poppler (pdftotext) for PDF imports.')
            process=subprocess.run(['pdftotext','-layout',str(path),'-'],capture_output=True,timeout=25)
            if process.returncode: raise ValueError('This PDF could not be read.')
            text=process.stdout.decode('utf-8','replace')
            method='pdftotext'
            if len(text.strip())<20:
                if not shutil.which('pdftoppm') or not shutil.which('tesseract'):
                    raise ValueError('Scanned PDF needs pdftoppm and Tesseract installed.')
                subprocess.run(['pdftoppm','-f','1','-l','3','-r','150','-png',str(path),str(Path(tmp)/'page')],check=True,capture_output=True,timeout=40)
                text='\n'.join(subprocess.run(['tesseract',str(page),'stdout'],capture_output=True,timeout=25).stdout.decode('utf-8','replace') for page in sorted(Path(tmp).glob('page-*.png')))
                method='Tesseract OCR (first three pages)'
        else:
            if not shutil.which('tesseract'): raise ValueError('Tesseract is required for image OCR.')
            process=subprocess.run(['tesseract',str(path),'stdout'],capture_output=True,timeout=30)
            if process.returncode: raise ValueError('The image could not be read.')
            text=process.stdout.decode('utf-8','replace');method='Tesseract OCR'
    pairs=[]
    for line in text.splitlines():
        match=re.match(r'^\s*([^:]{2,65}):\s*(.+)$',line)
        if match: pairs.append((match[1].strip(),match[2].strip()))
    if not pairs: raise ValueError('No labelled fields found. Use the source text to enter the intake manually.')
    source=normalize_table([[p[0] for p in pairs],[p[1] for p in pairs]],filename,'uploaded document',0)
    source['extraction_tool']=method;source['extracted_text']=text[:15000]
    source['note']='Review extracted fields against the original document before populating apps.'
    return source


def import_file(blob, name):
    """Choose the right reader for an uploaded file by extension and return its normalized table.

    Files over 8 MB or of unsupported types are rejected with a ValueError.
    """
    if len(blob)>8_000_000: raise ValueError('Use a file smaller than 8 MB for this local demo.')
    ext=Path(name).suffix.lower()
    if ext=='.xlsx': return normalize_table(read_xlsx(blob),name,'uploaded Excel workbook')
    if ext in ['.csv','.tsv','.txt']: return normalize_table(read_csv(blob),name,'uploaded delimited file')
    if ext in ['.pdf','.png','.jpg','.jpeg']: return extract_document(blob,name)
    raise ValueError('Supported files: XLSX, CSV, TSV, PDF, PNG, JPG.')


class SafeRedirect(urllib.request.HTTPRedirectHandler):
    """HTTP redirect handler that only follows redirects to Google spreadsheet hosts."""
    def redirect_request(self,req,fp,code,msg,headers,newurl):
        """Reject any redirect (for example to a sign-in page) that leaves the allowed Google hosts."""
        host=urllib.parse.urlsplit(newurl).hostname or ''
        if not (host=='docs.google.com' or host.endswith('.googleusercontent.com')):
            raise ValueError('Source redirected to a sign-in page or unsupported host. Use a public demo sheet.')
        return super().redirect_request(req,fp,code,msg,headers,newurl)


def fetch_bytes(url, google=False):
    """Download a URL and return (body bytes, HTTP status).

    Only the Google Sheets and OpenF1 hosts are allowed. Responses are limited to 8 MB,
    HTML pages are rejected, and common HTTP failures become readable ValueErrors.
    """
    host=urllib.parse.urlsplit(url).hostname
    if host not in ['docs.google.com','api.openf1.org']:
        raise ValueError('Only Google Sheets and OpenF1 source hosts are supported.')
    opener=urllib.request.build_opener(SafeRedirect()) if google else urllib.request.build_opener()
    req=urllib.request.Request(url,headers={'User-Agent':'Relayworks-Local-Demo/1.0','Accept':'text/csv,application/json'})
    try:
        with opener.open(req,timeout=20) as response:
            data=response.read(8_000_001)
            if len(data)>8_000_000: raise ValueError('Source exceeds the 8 MB import limit.')
            if 'text/html' in response.headers.get('Content-Type',''):
                raise ValueError('The sheet returned a web page. Publish a demo tab or enable viewer-link access.')
            return data, response.status
    except urllib.error.HTTPError as error:
        if error.code in [401,403]: raise ValueError('This source requires access. Use a public demo sheet; private Google authorization is not configured.') from error
        if error.code==429: raise ValueError('Provider rate limit reached. Wait before refreshing; existing data is retained.') from error
        raise ValueError(f'Provider returned HTTP {error.code}. Existing imported data is retained.') from error
    except urllib.error.URLError as error:
        raise ValueError('Could not reach the source. Check the connection and try again.') from error


def google_sheet(url):
    """Fetch a public Google Sheets tab as CSV and return it as a normalized table.

    Accepts normal and "published to web" sheet URLs and records the request details
    and a hash of the downloaded data so the result can be traced.
    """
    parts=urllib.parse.urlsplit(url.strip())
    if parts.scheme!='https' or parts.hostname!='docs.google.com':
        raise ValueError('Enter an https://docs.google.com/spreadsheets/ URL.')
    query=urllib.parse.parse_qs(parts.query);fragment=urllib.parse.parse_qs(parts.fragment)
    gid=(query.get('gid') or fragment.get('gid') or ['0'])[0]
    if not gid.isdigit(): raise ValueError('The sheet tab ID must be numeric.')
    published=re.match(r'^/spreadsheets/d/e/([\w-]+)',parts.path)
    standard=re.match(r'^/spreadsheets/d/([\w-]+)',parts.path)
    if published: export=f'https://docs.google.com/spreadsheets/d/e/{published[1]}/pub?output=csv&gid={gid}'
    elif standard: export=f'https://docs.google.com/spreadsheets/d/{standard[1]}/export?format=csv&gid={gid}'
    else: raise ValueError('The URL does not identify a Google spreadsheet.')
    blob,status=fetch_bytes(export,True)
    source=normalize_table(read_csv(blob),'Google Sheets · tab '+gid,'live Google Sheets fetch')
    source.update(url=url,request_url=export,http_status=status,auth='Public viewer access; no key',cost='No paid API dependency; public export availability is controlled by Google.',raw_hash=hashlib.sha256(blob).hexdigest())
    return source


def openf1(session='9158',driver='1'):
    """Fetch historical Formula 1 driver, lap, and session data from the OpenF1 public API.

    Returns a one-row normalized table (best lap, laps counted) plus the request log.
    """
    if not str(session).isdigit() or not str(driver).isdigit(): raise ValueError('Session and driver IDs must be numeric.')
    base='https://api.openf1.org/v1/'
    endpoints=[f'drivers?session_key={session}&driver_number={driver}',f'laps?session_key={session}&driver_number={driver}',f'sessions?session_key={session}']
    results=[]; requests=[]
    for endpoint in endpoints:
        blob,status=fetch_bytes(base+endpoint)
        results.append(json.loads(blob));requests.append({'method':'GET','url':base+endpoint,'status':status,'fetched_at':now()})
    drivers,laps,sessions=results
    if not drivers or not laps or not sessions: raise ValueError('No historical results for those IDs. Try session 9158 and driver 1.')
    person=drivers[0];session_data=sessions[0]
    durations=[r['lap_duration'] for r in laps if isinstance(r.get('lap_duration'),(int,float)) and r['lap_duration']>0]
    source=normalize_table([
        ['event_ref','Team / driver','Event / session','Event date','Result / best lap','Laps counted'],
        [f'F1-{session}-{driver}',person.get('full_name',f'Driver {driver}'),f"{session_data.get('location','')} · {session_data.get('session_name','')}",session_data.get('date_start',''),f'{min(durations):.3f} seconds' if durations else 'Not available',len(laps)]
    ],'OpenF1 · historical driver report','historical public API data',0)
    source.update(requests=requests,url='https://openf1.org/docs/',auth='Historical public endpoint; no key',cost='$0 historical access. Live data is a separate paid service.',provider_date=session_data.get('date_start'),raw_records={'driver':person,'session':session_data,'laps':laps})
    return source


def xlsx_bytes(matrix):
    """Build a minimal single-sheet .xlsx file from a grid of values and return its bytes.

    Numbers are stored as numbers and everything else as escaped text.
    """
    def col_name(index):
        """Convert a 1-based column number to spreadsheet letters (1 -> A, 27 -> AA)."""
        result=''
        while index: index,rem=divmod(index-1,26);result=chr(65+rem)+result
        return result
    rows=[]
    for r,row in enumerate(matrix,1):
        cells=[]
        for c,value in enumerate(row,1):
            address=f'{col_name(c)}{r}'
            if isinstance(value,(int,float)) and not isinstance(value,bool):
                cells.append(f'<c r="{address}"><v>{value}</v></c>')
            else:
                cells.append(f'<c r="{address}" t="inlineStr"><is><t xml:space="preserve">{html.escape(str(value))}</t></is></c>')
        rows.append(f'<row r="{r}">'+''.join(cells)+'</row>')
    # An .xlsx file is a zip of small XML parts; write the required parts by hand.
    mem=io.BytesIO()
    with zipfile.ZipFile(mem,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<?xml version="1.0"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/></Types>')
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Import" sheetId="1" r:id="rId1"/></sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/></Relationships>')
        z.writestr('xl/worksheets/sheet1.xml','<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData>'+''.join(rows)+'</sheetData></worksheet>')
    return mem.getvalue()


def pdf_bytes(title, lines, subtitle='Synthetic demonstration data · Relayworks'):
    """Build a simple multi-page text PDF (title bar, subtitle, wrapped lines) and return its bytes.

    Written directly in PDF syntax with the built-in Helvetica font, so no PDF library is needed.
    """
    def esc(text):
        """Replace characters the basic font cannot show and escape PDF string delimiters."""
        for old,new in [('—','-'),('–','-'),('→','->'),('’',"'")]: text=str(text).replace(old,new)
        return str(text).replace('\\','\\\\').replace('(','\\(').replace(')','\\)')
    wrapped=[]
    for line in lines: wrapped += textwrap.wrap(str(line),87) or ['']
    # Wrap lines to 87 characters and split into pages of 37 lines.
    chunks=[wrapped[i:i+37] for i in range(0,len(wrapped),37)] or [[]]
    objects=[b'',b'',b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    page_ids=[]
    for index,chunk in enumerate(chunks):
        page_id=len(objects)+1;stream_id=page_id+1;page_ids.append(page_id)
        commands=['0.06 0.45 0.40 rg 0 730 612 62 re f',
                  f'BT /F1 19 Tf 1 1 1 rg 40 757 Td ({esc(title[:65])}) Tj ET',
                  f'BT /F1 9 Tf 0.3 0.35 0.4 rg 40 706 Td ({esc(subtitle[:95])}) Tj ET']
        for row,line in enumerate(chunk):
            commands.append(f'BT /F1 10 Tf 0.13 0.18 0.23 rg 40 {677-row*16} Td ({esc(line)}) Tj ET')
        commands.append(f'BT /F1 9 Tf 0.4 0.4 0.4 rg 40 35 Td (Relayworks / page {index+1} / inspect source and run history for provenance) Tj ET')
        stream='\n'.join(commands).encode('latin-1','replace')
        objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {stream_id} 0 R >>'.encode())
        objects.append(f'<< /Length {len(stream)} >>\nstream\n'.encode()+stream+b'\nendstream')
    objects[0]=b'<< /Type /Catalog /Pages 2 0 R >>'
    objects[1]=('<< /Type /Pages /Count '+str(len(page_ids))+' /Kids ['+' '.join(f'{i} 0 R' for i in page_ids)+'] >>').encode()
    # Assemble the file: header, numbered objects, then the cross-reference table
    # with each object's byte offset, and the trailer.
    output=bytearray(b'%PDF-1.4\n');offsets=[0]
    for i,obj in enumerate(objects,1):
        offsets.append(len(output));output.extend(f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n')
    xref=len(output);output.extend(f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode())
    for offset in offsets[1:]:output.extend(f'{offset:010} 00000 n \n'.encode())
    output.extend(f'trailer << /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode())
    return bytes(output)


def messy_matrix(scenario):
    """Create a deliberately untidy sample sheet for a scenario (title rows, extra spaces,
    bad email, odd phone and money formats, ambiguous date, a near-duplicate row).

    Used to demonstrate cleanup; all values are synthetic.
    """
    fields=scenario['fields'];head=[f['label'] for f in fields]
    first=[f['default'] for f in fields]
    for i,f in enumerate(fields):
        if f['key']=='full_name':first[i]='  '+str(first[i]).replace(' ','   ')+'  '
        if f['key']=='email':first[i]='  '+str(first[i]).upper()+' '
        if f['key']=='phone':first[i]='(555) 555-0146'
        if f['type']=='number':first[i]=f'$ {first[i]}' if any(x in f['key'] for x in ['fee','cost','price','estimate']) else first[i]
    second=list(first)
    for i,f in enumerate(fields):
        if f['key']==scenario['primary']:second[i]=str(f['default'])+'-B'
        if f['key']=='full_name':second[i]='Taylor Sample'
        if f['key']=='email':second[i]='missing-at-sign.example.invalid'
        if f['key'] in ['slot','event_date','appointment']:second[i]='03/04/26'
    return [[scenario['company'].upper()+' / OLD WORKBOOK — DO NOT DELETE'],['Export copied from three office tabs'],[],['  '+h.upper()+'  ' for h in head],first,[],second,list(first)]
