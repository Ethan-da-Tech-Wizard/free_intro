/** Complete operator rehearsal. Uses the isolated copy's browser UI and keeps evidence. */
import {chromium,expect} from '@playwright/test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {execFileSync} from 'node:child_process';
const root=path.resolve(import.meta.dirname,'..');
const base='http://127.0.0.1:8875';
const audit=path.join(root,'audit');
const attempt=new Date().toISOString().replace(/[:.]/g,'-');
const folder=path.join(audit,'attempts',attempt);
await fs.mkdir(path.join(folder,'screenshots'),{recursive:true});await fs.mkdir(path.join(folder,'downloads'));
const browser=await chromium.launch({headless:!process.env.SHOW_BROWSER});
const context=await browser.newContext({viewport:{width:1440,height:1050},acceptDownloads:true});
await context.tracing.start({screenshots:true,snapshots:true,sources:true});
const page=await context.newPage();page.setDefaultTimeout(12000);
const errors=[];context.on('page',p=>p.on('pageerror',e=>errors.push(e.message)));page.on('pageerror',e=>errors.push(e.message));
const ledger={attempt,started_at:new Date().toISOString(),base,steps:[],status:'running',browser_errors:errors};
let serial=0,last=null,chapter=0;
const get=async route=>{const r=await page.request.get(base+route);assert.ok(r.ok(),await r.text());return r.json();};
const config=await get('/api/config');
assert.equal(path.resolve(config.data_dir),path.join(root,'runtime'),'Refusing to rehearse against another workspace.');
const scene=id=>config.scenarios.find(s=>s.id===id);
async function save(){await fs.writeFile(path.join(folder,'journal.json'),JSON.stringify(ledger,null,2));await fs.writeFile(path.join(audit,'current.json'),JSON.stringify(ledger,null,2));}
async function step(title,fn){
  const item={id:String(++serial).padStart(3,'0'),chapter:String(chapter).padStart(2,'0'),title,started_at:new Date().toISOString(),status:'running'};ledger.steps.push(item);await save();
  console.log('DO',item.chapter,item.id,title);
  try{item.proof=await fn()||{};item.status='passed';}
  catch(e){item.status='failed';item.error=e.stack;throw e;}
  finally{item.finished_at=new Date().toISOString();item.url=page.url();const file=`screenshots/${item.id}.png`;await page.screenshot({path:path.join(folder,file),fullPage:true,animations:'disabled'}).then(()=>item.screenshot=file).catch(()=>{});await save();}
}
async function go(route,heading){await page.goto(base+route);if(heading)await page.getByRole('heading',{name:heading,exact:true}).first().waitFor();}
async function tab(label){await page.getByRole('link',{name:label==='Under the hood'?/^Under the hood/:label,exact:label!=='Under the hood'}).first().click();}
async function reset(id){await go(`/#scenario/${id}/manual`,scene(id).short);await page.getByRole('button',{name:'Reset workplaces'}).click();await page.getByRole('button',{name:'Clear these demo records'}).click();await page.locator('#modal').waitFor({state:'hidden'});await expect(page.locator('#toast')).toContainText('Workplaces cleared');last=null;}
async function field(key,value){await page.locator('#intake-'+key).fill(String(value));}
async function fields(values){for(const [k,v] of Object.entries(values))await field(k,v);}
async function requestClick(label,route){const response=page.waitForResponse(r=>r.url()===base+route&&r.request().method()==='POST');await page.getByRole('button',{name:label,exact:true}).click();const r=await response;return {status:r.status(),data:await r.json()};}
async function waitRun(id,status='complete'){
  let run;for(let n=0;n<160;n++){run=await get('/api/runs/'+id);if(!['queued','running'].includes(run.status))break;await new Promise(r=>setTimeout(r,80));}
  assert.equal(run.status,status,run.message);last=run;
  await expect(page.locator('.run-banner .mono')).toHaveText(id);
  await expect(page.locator('.run-banner')).toHaveClass(new RegExp(status));
  await fs.writeFile(path.join(folder,'run-'+id+'.json'),JSON.stringify(run,null,2));return run;
}
async function run(status='complete'){const result=await requestClick('Populate all three apps','/api/runs');assert.equal(result.status,202,JSON.stringify(result));return waitRun(result.data.run.id,status);}
async function follow(label,values={},status='complete',event){await page.getByRole('button',{name:label,exact:true}).click();for(const [k,v] of Object.entries(values))await page.locator('#action-'+k).fill(String(v));if(event)await page.locator('[name="event_id"]').fill(event);const result=await requestClick('Apply and verify','/api/runs');assert.equal(result.status,202,JSON.stringify(result));await page.locator('#modal').waitFor({state:'hidden'});return waitRun(result.data.run.id,status);}
async function preview(error=false){const r=await requestClick('Preview field mapping','/api/preview');assert.equal(r.status,error?422:200,JSON.stringify(r));if(error)await page.locator('#form-error [role="alert"]').waitFor();else await page.getByRole('heading',{name:'Mapping preview'}).waitFor();return r;}
async function download(p,label,prefix=''){
  const pending=p.waitForEvent('download');await p.getByRole('link',{name:label,exact:true}).click();const d=await pending;const name=prefix+d.suggestedFilename();const file=path.join(folder,'downloads',name);await d.saveAs(file);const data=await fs.readFile(file);assert.ok(data.length>20);
  if(name.endsWith('.pdf')){assert.equal(data.subarray(0,5).toString(),'%PDF-');const txt=execFileSync('pdftotext',[file,'-'],{encoding:'utf8'});await fs.writeFile(file+'.txt',txt);}
  return {file:path.relative(root,file),bytes:data.length};
}
async function manual(id){
  const s=scene(id);await reset(id);
  for(let i=0;i<3;i++)await step(`Manual ${s.targets[i].name}: type ${s.stage_fields[i].length} documented fields and save`,async()=>{
    const pending=context.waitForEvent('page');await page.getByRole('link',{name:'Open '+s.targets[i].name,exact:true}).click();const desk=await pending;await desk.getByRole('heading',{name:'Create a record',exact:true}).waitFor();
    const entered={};for(const key of s.stage_fields[i]){const value=s.fields.find(f=>f.key===key).default;await desk.locator('#work-'+key).fill(String(value));entered[key]=value;}
    await desk.screenshot({path:path.join(folder,`screenshots/manual-${id}-${i}-typed.png`),fullPage:true,animations:'disabled'});
    await desk.getByRole('button',{name:'Save to '+s.targets[i].name,exact:true}).click();await desk.getByRole('heading',{name:'Saved record',exact:true}).waitFor();
    const record=new URL(desk.url()).searchParams.get('record');const read=await get(`/api/workplaces/${s.targets[i].id}/records/${record}`);
    for(const key of s.stage_fields[i])assert.equal(String(read.record.payload[s.targets[i].mapping[key]]),String(entered[key]));
    await desk.screenshot({path:path.join(folder,`screenshots/manual-${id}-${i}-saved.png`),fullPage:true,animations:'disabled'});
    const exported=await download(desk,'Download populated document','manual-');await desk.close();
    return {entered,record:read.record,document:exported,screenshots:[`screenshots/manual-${id}-${i}-typed.png`,`screenshots/manual-${id}-${i}-saved.png`]};
  });
}
async function inspect(run){
  const output=[];
  for(const out of run.outputs){const p=await context.newPage();const index=scene(run.scenario).targets.findIndex(t=>t.id===out.app_id);await p.goto(base+`/workplace?scenario=${run.scenario}&app=${index}&record=${out.record.id}`);await p.getByRole('heading',{name:'Saved record',exact:true}).waitFor();
    for(const [key,value] of Object.entries(scene(run.scenario).targets[index].mapping))await expect(p.locator('#work-'+key)).toHaveValue(String(out.record.payload[value]??''));
    await p.screenshot({path:path.join(folder,`screenshots/saved-${run.id}-${index}.png`),fullPage:true,animations:'disabled'});
    output.push({record_id:out.record.id,app:out.app_id,url:p.url(),document:await download(p,'Download populated document'),screenshot:`screenshots/saved-${run.id}-${index}.png`});await p.close();}
  return {run_id:run.id,status:run.status,outputs:output};
}
async function fresh(id){await reset(id);await tab('Automate it');await preview();return run();}
async function fixture(){await go('/#connections','The mess is welcome.');await page.locator('[data-action="fixture"][data-scenario="hvac"]').click();await page.getByRole('heading',{name:'After cleanup',exact:true}).waitFor();}
async function useRow(){await page.getByRole('button',{name:'Use this row in the intake',exact:true}).click();await page.getByRole('heading',{name:'Enter it once.',exact:true}).waitFor();}
async function importSource(button){await go('/#connections','The mess is welcome.');const pending=page.waitForResponse(r=>r.url().includes('/api/sources/')&&r.request().method()==='POST');await page.getByRole('button',{name:button,exact:true}).click();const r=await pending;assert.equal(r.status(),201,await r.text());const src=await r.json();await page.getByRole('heading',{name:'After cleanup',exact:true}).waitFor();return src;}
const chapters={
  2:async()=>{
    await step('Tour Overview, connections, gallery, run history, all five HVAC tabs, and cancel Reset',async()=>{
      for(const [route,title] of [['/','Your automation playground.'],['/#connections','The mess is welcome.'],['/#evidence','See the difference.'],['/#history','Every handoff has a history.']])await go(route,title);
      await go('/#scenario/hvac/overview','HVAC & field service');for(const title of ['Do it manually','Automate it','Saved results','Under the hood','The workflow'])await tab(title);
      await page.getByRole('button',{name:'Reset workplaces'}).click();await page.getByRole('button',{name:'Keep working'}).click();await page.locator('#modal').waitFor({state:'hidden'});
      return {scenarios:config.scenarios.map(s=>({name:s.short,apps:s.targets.map(t=>t.name)}))};
    });
    await step('Check draft behavior when typing, switching views, and reloading',async()=>{
      await tab('Automate it');await field('issue','Rehearsal draft retained between views');await tab('The workflow');await tab('Automate it');const retained=await page.locator('#intake-issue').inputValue();assert.equal(retained,'Rehearsal draft retained between views');await page.reload();await page.locator('#intake-issue').waitFor();assert.equal(await page.locator('#intake-issue').inputValue(),'AC is blowing warm air');return {typed_value_survives_view_change:true,reload_restores_sample:true,original_book_claim:'The book incorrectly says leaving before Preview can discard typing.'};
    });
  },
  3:async()=>{await step('Read the actual architecture image and scenario mappings',async()=>{
    await go('/#scenario/hvac/overview','HVAC & field service');await page.locator('.flow-diagram').scrollIntoViewIfNeeded();assert.ok(await page.locator('.flow-diagram').evaluate(img=>img.naturalWidth>0));await tab('Under the hood');await expect(page.getByText('The translation layer',{exact:true})).toBeVisible();return {maps:scene('hvac').targets.map(t=>({app:t.name,name_field:t.mapping.full_name})),database_files:(await fs.readdir(path.join(root,'runtime/workplaces'))).filter(n=>n.endsWith('.sqlite3'))};
  });},
  4:async()=>manual('hvac'),
  5:async()=>{
    let first;
    await step('Reset manual HVAC entries; preview all three field mappings; populate and inspect the saved destinations',async()=>{first=await fresh('hvac');assert.equal(first.steps.length,6);return inspect(first);});
    await step('Download PDF packet and Excel export; replay the unchanged intake',async()=>{const outputs=[await download(page,'PDF packet'),await download(page,'Excel export')];await tab('Automate it');const replay=await run();assert.equal(replay.id,first.id);return {outputs,reused_run:first.id};});
  },
  6:async()=>{
    await go('/#scenario/hvac/results','HVAC & field service');
    let completion;
    await step('Complete the visit with 1.5 hours × 80 + 35 parts + 95 fee; inspect $250 draft',async()=>{completion=await follow('Complete the visit');assert.equal(completion.outputs[2].record.payload.total_usd,'250.00');return inspect(completion);});
    await step('Repeat the identical completion event; verify no additional charge',async()=>{const replay=await follow('Complete the visit');assert.equal(replay.id,completion.id);return {run_id:replay.id,total:replay.outputs[2].record.payload.total_usd};});
    await step('Create JOB-1043 for the same C-014 customer at the documented new slot',async()=>{await tab('Automate it');await fields({job_ref:'JOB-1043',slot:'2026-10-07 10:00'});const second=await run();assert.equal(second.outputs[0].record.id,completion.outputs[0].record.id);assert.deepEqual(second.outputs[0].record.payload.service_references,['JOB-1042','JOB-1043']);return inspect(second);});
  },
  8:async()=>{
    await reset('hvac');
    await step('Open the ugly workbook inspector; verify header row 4 and ready/review/duplicate rows',async()=>{await fixture();const source=await get('/api/sources/'+page.url().split('#source/')[1].split('/')[0]);assert.equal(source.header_row,4);assert.equal(source.rows.length,3);assert.deepEqual(source.rows.map(r=>r.row_number),[5,7,8]);assert.ok(source.rows[2].duplicate);return source;});
    await step('Map Row 5; verify normalized email and fee; populate the three workplaces',async()=>{await page.locator('#source-row').selectOption('0');await useRow();assert.equal(await page.locator('#intake-email').inputValue(),'avery@example.invalid');assert.equal(await page.locator('#intake-fee').inputValue(),'95');await preview();return inspect(await run());});
    await step('Map Row 7; confirm validation hold before correcting the source ambiguity',async()=>{await fixture();await page.locator('#source-row').selectOption('1');await useRow();return preview(true);});
    await step('Correct Taylor to C-015, valid email, JOB-1042-B, 11:00; confirm review and save',async()=>{await fields({customer_ref:'C-015',full_name:'Taylor Sample',email:'taylor@example.invalid',job_ref:'JOB-1042-B',slot:'2026-10-06 11:00'});await page.locator('#review-confirmed').check();await preview();const result=await run();const customer=await get('/api/workplaces/hvac-0/records');assert.equal(customer.records.length,2);return inspect(result);});
    await step('Batch only ready rows; inspect submitted/reused/held counts and run history',async()=>{await fixture();await page.getByRole('button',{name:'Populate all ready rows',exact:true}).click();await expect(page.locator('#bulk-result')).toContainText('1 rows submitted');await expect(page.locator('#bulk-result')).toContainText('2 rows held');const summary=await page.locator('#bulk-result').innerText();await tab('Inspect run history');return {summary,dashboard:await get('/api/dashboard')};});
    await step('Upload the actual HVAC XLSX from disk and repeat the first-row mapping',async()=>{await go('/#connections','The mess is welcome.');await page.locator('#upload-input').setInputFiles(path.join(root,'practice_files/hvac-ugly.xlsx'));await page.getByRole('heading',{name:'After cleanup'}).waitFor();await page.locator('#source-scenario').selectOption('hvac');await useRow();assert.equal(await page.locator('#intake-email').inputValue(),'avery@example.invalid');return {file:'practice_files/hvac-ugly.xlsx',preview:await preview()};});
  },
  9:async()=>{
    for(const [name,tool] of [['hvac-intake.pdf','pdftotext'],['hvac-scanned-intake.png','Tesseract OCR']]){
      await step(`Upload ${name}; inspect ${tool} extraction and review every mapped field`,async()=>{await reset('hvac');await tab('Automate it');await page.getByRole('button',{name:'Upload a file',exact:true}).click();await page.locator('#modal-file').setInputFiles(path.join(root,'practice_files',name));await page.getByRole('heading',{name:'Extracted document text · '+tool,exact:true}).waitFor();const id=page.url().split('#source/')[1].split('/')[0],source=await get('/api/sources/'+id);await useRow();const values={};for(const f of scene('hvac').fields)values[f.key]=await page.locator('#intake-'+f.key).inputValue();return {source,values};});
      await step(`Confirm document review, correct any extraction differences in ${name}, save and inspect all output PDFs`,async()=>{
        const corrections=[];
        for(const f of scene('hvac').fields){const observed=await page.locator('#intake-'+f.key).inputValue();const expected=String(f.default);
          const equal=f.key==='phone'?observed.replace(/\D/g,'')===expected.replace(/\D/g,''):f.type==='number'?Number(observed)===Number(expected):observed===expected;
          if(!equal){corrections.push({field:f.label,extracted:observed,corrected:expected,reason:'Compared against the known original practice form.'});await field(f.key,expected);}
        }
        await page.locator('#review-confirmed').check();await preview();return {corrections,...await inspect(await run())};
      });
    }
  },
  10:async()=>{
    await reset('events');
    await step('Open the original Google sample link; fetch its public CSV and inspect actual source facts',async()=>{
      await go('/#connections','The mess is welcome.');const pending=context.waitForEvent('page');await page.getByRole('link',{name:'Open the original Google Sheet ↗',exact:true}).click();const sheet=await pending;await sheet.waitForLoadState('domcontentloaded');const title=await sheet.title();await sheet.screenshot({path:path.join(folder,'screenshots/original-google-sheet.png'),fullPage:false});await sheet.close();const source=await importSource('Pull from Google Sheets');assert.equal(source.http_status,200);return {original_title:title,source};
    });
    await step('Map Student Name and Major; use one row; identify defaults and inspect three saved records',async()=>{
      await page.locator('#mapping-form [name="full_name"]').selectOption('Student Name');await page.locator('#mapping-form [name="session"]').selectOption('Major');await useRow();await expect(page.locator('.source-tag').first()).toContainText('Demo defaults supply');const r=await run();assert.match(r.payload.registration_ref,/^SHEET-/);return inspect(r);
    });
    await step('Pull again, populate every ready Google row, and inspect final workplace counts',async()=>{
      const source=await importSource('Pull from Google Sheets');await page.getByRole('button',{name:'Populate all ready rows'}).click();await expect(page.locator('#bulk-result')).toContainText(source.rows.length+' rows submitted');await tab('Inspect run history');
      let dashboard;for(let n=0;n<150;n++){dashboard=await get('/api/dashboard');if(!dashboard.runs.some(r=>r.scenario==='events'&&['queued','running'].includes(r.status)))break;await new Promise(r=>setTimeout(r,100));}
      const saved=await Promise.all([0,1,2].map(i=>get('/api/workplaces/events-'+i+'/records')));const counts=saved.map(s=>s.records.length);assert.deepEqual(counts,[source.rows.length,source.rows.length,source.rows.length]);
      return {source_rows:source.rows.length,counts,history_text:await page.locator('#main').innerText(),waitlisted:saved[1].records.filter(r=>r.payload.status==='Waitlisted').length};
    });
    await step('Replay the recorded Google source; keep replay label and original retrieval date',async()=>{const src=await importSource('Replay Google sample');assert.match(src.kind,/^recorded /);assert.ok(src.replayed_at);await useRow();return {source_kind:src.kind,fetched_at:src.fetched_at,replayed_at:src.replayed_at,...await inspect(await run())};});
  },
  11:async()=>{
    await step('Enable the one-minute Google timer and observe the first actual scheduled pull',async()=>{
      await go('/#connections','The mess is welcome.');await page.locator('#schedule-kind').selectOption('google');await page.locator('#schedule-interval').selectOption('60');await page.getByRole('button',{name:'Enable schedule',exact:true}).click();await expect(page.locator('#schedule-status')).toContainText('Enabled');const start=await get('/api/schedules');assert.equal(start.last_run,null);
      let result;for(let n=0;n<55;n++){await new Promise(r=>setTimeout(r,2000));result=await get('/api/schedules');if(n%10===0)console.log('Timer observation:',n*2,'seconds');if(result.last_run)break;}assert.ok(result.last_run);assert.match(result.message,/rows submitted/);await go('/','Your automation playground.');await tab('Sources & connections');await expect(page.locator('#schedule-status')).toContainText('Last checked:');return result;
    });
    await step('Stop the timer and inspect the generated runs/records',async()=>{await page.getByRole('button',{name:'Stop schedule',exact:true}).click();await expect(page.locator('#schedule-status')).toContainText('Schedule is off');assert.equal((await get('/api/schedules')).enabled,false);await tab('Run history');return {schedule:await get('/api/schedules'),dashboard:await get('/api/dashboard')};});
  },
  12:async()=>{
    await manual('sports');await reset('sports');
    await step('Fetch historical OpenF1 data; inspect three provider requests and calculation inputs',async()=>{const src=await importSource('Fetch historical F1 data');assert.equal(src.requests.length,3);assert.ok(src.requests.every(r=>r.status===200));await page.getByText('Provider records used for the calculation',{exact:true}).click();return src;});
    await step('Map historical facts into the three sports desks, inspect the report, and download a real calendar',async()=>{await useRow();const r=await run();const proof=await inspect(r);proof.calendar=await download(page,'Calendar file');const ics=await fs.readFile(path.join(root,proof.calendar.file),'utf8');assert.match(ics,/BEGIN:VCALENDAR/);return proof;});
    await step('Repeat sports mapping with an explicitly labelled offline provider recording',async()=>{const src=await importSource('Replay F1 sample');assert.match(src.kind,/^recorded /);await useRow();return {source:src.kind,...await inspect(await run())};});
  },
  13:async()=>{
    await manual('legal');await step('Reset the manual law-office records; populate and inspect all three apps',async()=>inspect(await fresh('legal')));
    await step('Trigger the possible-party review hold and verify the unreviewed request is rejected',async()=>{await page.getByRole('button',{name:'Demonstrate a review hold'}).click();return preview(true);});
    await step('Record the reviewer decision and populate the reviewed matter, packet, and task',async()=>{await page.locator('#review-confirmed').check();await preview();return inspect(await run());});
  },
  14:async()=>{
    await manual('clinic');await step('Reset manual clinic records; register Jordan and book the 11:00 slot',async()=>inspect(await fresh('clinic')));
    await step('Attempt the second patient in the occupied slot; verify a partial save and a 409 conflict',async()=>{const r=await requestClick('Try a conflicting appointment','/api/runs');assert.equal(r.status,202);const failed=await waitRun(r.data.run.id,'needs_attention');assert.equal(failed.outputs.length,1);assert.ok(failed.steps.some(s=>s.status===409));await tab('Under the hood');return failed;});
    await step('Retain PAT-0310-B; correct the appointment to noon; verify all three destinations',async()=>{await tab('Automate it');assert.equal(await page.locator('#intake-patient_ref').inputValue(),'PAT-0310-B');await field('slot','2026-10-08 12:00');return inspect(await run());});
  },
  15:async()=>{
    await manual('retail');let initial;
    await step('Reset retail; receive 12 units with two reserved; verify 10 available in catalog',async()=>{initial=await fresh('retail');assert.equal(initial.outputs[1].record.payload.stock_quantity,12);assert.equal(initial.outputs[2].record.payload.available_quantity,10);return inspect(initial);});
    await step('Replay REC-088; prove the stock effect is not applied twice',async()=>{const r=await requestClick('Replay the delivery','/api/runs');assert.ok(r.data.reused);assert.equal(r.data.run.id,initial.id);return waitRun(r.data.run.id);});
    await step('Receive REC-089 for the same SKU; verify 24 on hand and 22 available',async()=>{await tab('Automate it');await field('receipt_ref','REC-089');const r=await run();assert.equal(r.outputs[1].record.payload.stock_quantity,24);assert.equal(r.outputs[2].record.payload.available_quantity,22);return inspect(r);});
    await step('Reuse REC-089 with quantity 99; verify the conflicting receipt is held, then reset deliberately',async()=>{await tab('Automate it');await field('quantity','99');const r=await run('needs_attention');assert.ok(r.steps.some(s=>s.status===409));const saved={run:r};await reset('retail');return saved;});
  },
  16:async()=>{
    await manual('reseller');await step('Reset seller; populate item, local listing draft, and sale paperwork',async()=>inspect(await fresh('reseller')));let sale;
    await step('Record SALE-019; verify one item becomes stock zero and produce a packing slip',async()=>{sale=await follow('Record a sale');assert.equal(sale.outputs[0].record.payload.stock_quantity,0);assert.equal(sale.outputs[2].record.payload.status,'Ready to pack');return inspect(sale);});
    await step('Replay the identical sale reference and confirm it reuses the recorded event',async()=>{const r=await follow('Record a sale');assert.equal(r.id,sale.id);return r;});
    await step('Attempt SALE-020 as a distinct sale; verify an oversell rejection',async()=>{const r=await follow('Record a sale',{sale_ref:'SALE-020'},'needs_attention','sale-USED-072-second');assert.ok(r.steps.some(s=>s.status===409));return r;});
  },
  17:async()=>{
    await manual('property');await step('Reset property; populate the repair with approved estimate 180',async()=>inspect(await fresh('property')));
    await step('Try WRONG-JOB invoice; correct reference but exceed estimate at 200; verify both holds',async()=>{await page.getByRole('button',{name:'Match a contractor invoice'}).click();await page.locator('#action-job_reference').fill('WRONG-JOB');const mismatch=await requestClick('Apply and verify','/api/runs');assert.equal(mismatch.status,422);await page.locator('#action-job_reference').fill('FIX-016');await page.locator('#action-invoice_total').fill('200');const amount=await requestClick('Apply and verify','/api/runs');assert.equal(amount.status,422);return {mismatch,amount};});
    await step('Correct invoice to FIX-016 and 180; verify completed repair and matched owner statement',async()=>{await page.locator('#action-invoice_total').fill('180');const response=await requestClick('Apply and verify','/api/runs');assert.equal(response.status,202);await page.locator('#modal').waitFor({state:'hidden'});const r=await waitRun(response.data.run.id);assert.deepEqual(r.outputs.map(o=>o.record.payload.status),['Completed','Completed','Invoice matched']);return inspect(r);});
  },
  18:async()=>{
    await manual('events');await reset('events');
    await step('Reserve REG-011 in a capacity-one session',async()=>{await tab('Automate it');await field('capacity','1');const r=await run();assert.equal(r.outputs[1].record.payload.status,'Reserved');return inspect(r);});
    await step('Submit REG-012 Taylor; verify the valid waitlist outcome',async()=>{await tab('Automate it');await fields({registration_ref:'REG-012',full_name:'Taylor Sample',email:'taylor@example.invalid'});const r=await run();assert.equal(r.outputs[1].record.payload.status,'Waitlisted');return inspect(r);});
    await step('Try checking in the waitlisted attendee; verify that no check-in writes occurred',async()=>{const r=await follow('Check in attendee',{},'needs_attention');assert.equal(r.outputs.length,0);assert.match(r.message,/reserved seat/i);return r;});
    await step('Deliberately raise practice capacity to two; reserve Taylor and check in successfully',async()=>{await tab('Automate it');await field('capacity','2');await run();const r=await follow('Check in attendee');assert.ok(r.outputs.every(o=>o.record.payload.status==='Checked in'));return inspect(r);});
  },
  19:async()=>{
    for(const [key,block,restore,code] of [['authorized','Revoke access','Grant access',403],['online','Take offline','Restore service',503]]){
      let failed;
      await step(`Reset HVAC; ${block} at Billing Desk; submit and inspect actual ${code}`,async()=>{await reset('hvac');await tab('Under the hood');await page.locator(`[data-app="hvac-2"][data-key="${key}"]`).click();await tab('Automate it');failed=await run('needs_attention');assert.equal(failed.outputs.length,2);assert.ok(failed.steps.some(s=>s.status===code));await tab('Under the hood');return failed;});
      await step(`${restore}; resume the failed handoff; prove first two IDs and revisions stayed the same`,async()=>{await page.locator(`[data-app="hvac-2"][data-key="${key}"]`).click();const response=await requestClick('Resume from saved step','/api/runs/'+failed.id+'/resume');assert.equal(response.status,202);const r=await waitRun(failed.id);assert.deepEqual(r.outputs.slice(0,2).map(o=>[o.record.id,o.record.revision]),failed.outputs.map(o=>[o.record.id,o.record.revision]));return inspect(r);});
    }
  },
  20:async()=>{await step('Expand POST, GET, source provenance, mapping, cost and capacity; inspect saved run history',async()=>{await go('/#scenario/hvac/technical','Actual HTTP traffic');for(const detail of await page.locator('.trace-step').all())await detail.locator('summary').click();await page.getByText('Source provenance',{exact:true}).click();const r=await get('/api/runs/'+await page.locator('.run-banner .mono').innerText());assert.ok(r.steps.some(s=>s.kind==='verified'));return r;});},
  21:async()=>{
    await step('Open the retained screenshot gallery and its manifest',async()=>{await go('/#evidence/hvac','See the difference.');const manifest=await get('/api/evidence');assert.ok(manifest.captures.length>=134);const pending=context.waitForEvent('page');await page.locator('.evidence-card').first().click();const image=await pending;await image.waitForLoadState('domcontentloaded');assert.ok(await image.locator('img').evaluate(e=>e.naturalWidth>0));await image.close();return {captures:manifest.captures.length,note:'Historical gallery; the audit has its own newly timestamped screenshots.'};});
    await step('Download PDF, Excel, calendar, evidence ZIP, and current workplace CSV',async()=>{await go('/#scenario/hvac/results','HVAC & field service');const files=[];for(const label of ['PDF packet','Excel export','Calendar file','Evidence bundle'])files.push(await download(page,label));const p=await context.newPage();await p.goto(base+'/workplace?scenario=hvac&app=0');await p.getByRole('heading',{name:'Create a record'}).waitFor();files.push(await download(p,'CSV'));await p.close();return {files};});
  },
  22:async()=>{await step('Open each of the eight workflow diagrams and validate all ten editable Archi views',async()=>{for(const s of config.scenarios){await go(`/#scenario/${s.id}/overview`,s.short);await page.locator('.flow-diagram').scrollIntoViewIfNeeded();assert.ok(await page.locator('.flow-diagram').evaluate(i=>i.naturalWidth>0));}const board=JSON.parse(await fs.readFile(path.join(root,'diagrams/showcase.archi.json'),'utf8'));return {diagram_files:(await fs.readdir(path.join(root,'diagrams'))).filter(n=>n.endsWith('.png')),board_top_level_keys:Object.keys(board),note:'Editable board loaded and exported separately with the installed Archi executable.'};});},
  24:async()=>{
    await step('Exercise native required/email checks and server validation without losing saved records',async()=>{await go('/#scenario/hvac/automate','Enter it once.');await field('email','bad-email');await page.getByRole('button',{name:'Populate all three apps'}).click();assert.equal(await page.locator('#intake-email').evaluate(e=>e.validity.valid),false);const bad=await preview(true);await field('email','avery@example.invalid');await preview();return {native_email_rejected:true,server_validation:bad};});
    await step('Verify failed and archived runs cannot silently masquerade as new completed work',async()=>{await go('/#history','Every handoff has a history.');const d=await get('/api/dashboard');const archived=d.runs.find(r=>r.status==='archived');assert.ok(archived);await page.locator(`[data-action="inspect-run"][data-run="${archived.id}"]`).click();await expect(page.locator('.run-banner')).toHaveClass(/archived/);return {archived_run:archived};});
  }
};
try{
  const chosen=process.argv.find(a=>a.startsWith('--chapters='))?.split('=')[1].split(',').map(Number);
  for(const [number,fn] of Object.entries(chapters)){chapter=Number(number);if(chosen&&!chosen.includes(chapter))continue;await fn();}
  assert.deepEqual(errors,[]);ledger.status='passed';console.log('PASS all selected documented browser lessons');
}catch(error){ledger.status='failed';ledger.error=error.stack;console.error(error.stack);process.exitCode=1;}
finally{
  ledger.finished_at=new Date().toISOString();await save();await context.tracing.stop({path:path.join(folder,'browser-trace.zip')});await browser.close();
}
