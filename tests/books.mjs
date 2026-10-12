/** Reader checks in isolated browser contexts and a separate demo server. */
import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import net from 'node:net';
import {pathToFileURL} from 'node:url';
import {spawn} from 'node:child_process';
const root=path.resolve(import.meta.dirname,'..');
const temp=await fs.mkdtemp(path.join(os.tmpdir(),'relaybooks-test-'));
const artifacts=path.join(root,'books/verification');await fs.mkdir(artifacts,{recursive:true});
async function port(){const s=net.createServer();await new Promise(r=>s.listen(0,'127.0.0.1',r));const p=s.address().port;await new Promise(r=>s.close(r));return p;}
const p=await port(),wp=await port(),base='http://127.0.0.1:'+p;
const server=spawn('python3',['app/server.py','--port',String(p),'--workplace-port',String(wp),'--data-dir',temp],{cwd:root,stdio:['ignore','pipe','pipe']});
let serverError='';server.stderr.on('data',v=>serverError+=v);server.stdout.resume();
const errors=[];const browser=await chromium.launch({headless:true});
async function ready(){for(let n=0;n<80;n++){try{if((await fetch(base+'/api/config')).ok)return;}catch{}await new Promise(r=>setTimeout(r,100));}throw Error('Server not ready: '+serverError);}
async function post(page,url,data){const r=await page.request.post(base+url,{data});assert.ok(r.ok(),await r.text());return r.json();}
async function apply(page,heading='Three destinations. Verified.'){
  const response=page.waitForResponse(r=>r.url()===base+'/api/runs'&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Apply and verify',exact:true}).click();assert.ok((await response).ok());
  await page.locator('#modal').waitFor({state:'hidden'});
  await page.getByRole('heading',{name:heading,exact:true}).waitFor();
}
try{
  await ready();
  const manifest=JSON.parse(await fs.readFile(path.join(root,'books/manifest.json'),'utf8'));
  for(const edition of ['file','http']){
    const context=await browser.newContext({viewport:{width:1440,height:1000},acceptDownloads:true});
    const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
    for(const m of manifest){
      await page.goto(edition==='file'?pathToFileURL(path.join(root,m.file)).href:base+'/'+m.file);
      assert.equal(await page.locator('.chapter').count(),m.chapters);
      assert.equal(await page.locator('[data-task]').count(),m.checkpoints);
      assert.equal(await page.locator('.chapter:visible').count(),1);
      assert.equal(await page.locator('body').innerText().then(x=>x.includes('{{')),false);
      const ids=await page.locator('[data-task]').evaluateAll(es=>es.map(e=>e.dataset.task));assert.equal(new Set(ids).size,ids.length);
      const first=page.locator('[data-task]').first();await first.check();
      const note=page.locator('[data-note]').first();await note.fill('Practice notes: checked source and saved result.');
      await page.reload();assert.equal(await first.isChecked(),true);assert.match(await note.inputValue(),/Practice notes/);
      const downloadPromise=page.waitForEvent('download');await page.getByRole('button',{name:'Export progress'}).click();const download=await downloadPromise;
      const saved=path.join(temp,m.id+'-'+edition+'.json');await download.saveAs(saved);
      const backup=JSON.parse(await fs.readFile(saved,'utf8'));assert.equal(backup.book,m.id);
      await first.uncheck();await note.fill('');await page.locator('#import-file').setInputFiles(saved);
      await page.getByRole('status').filter({hasText:'Progress imported.'}).waitFor();assert.equal(await first.isChecked(),true);assert.match(await note.inputValue(),/Practice notes/);
      const invalid=path.join(temp,'wrong-book.json');await fs.writeFile(invalid,JSON.stringify({...backup,book:'wrong'}));
      await page.locator('#import-file').setInputFiles(invalid);await page.getByRole('status').filter({hasText:'Import failed:'}).waitFor();assert.equal(await first.isChecked(),true);
      await page.locator('#import-file').setInputFiles(saved);await page.getByRole('status').filter({hasText:'Progress imported.'}).waitFor();
      await page.getByRole('button',{name:'Next chapter'}).click();assert.match(page.url(),/#chapter-01$/);assert.equal(await page.locator('.chapter:visible').count(),1);
      await page.getByRole('button',{name:'Read whole book'}).click();assert.equal(await page.locator('.chapter:visible').count(),m.chapters);
      await page.getByRole('button',{name:'One chapter at a time'}).click();
      await page.getByRole('searchbox',{name:'Search this book'}).fill('Google');assert.ok(await page.locator('.chapter:visible').count()>1);
      await page.getByRole('searchbox',{name:'Search this book'}).fill('unlikelysearchwordzz');assert.equal(await page.locator('.chapter:visible').count(),0);assert.equal(await page.locator('#no-results').isVisible(),true);
      await page.getByRole('searchbox',{name:'Search this book'}).fill('');
      await page.locator('[data-chapter-link="chapter-01"]').click();
      await page.screenshot({path:path.join(artifacts,m.id+'-'+edition+'-desktop.png'),fullPage:true,animations:'disabled'});
      await page.setViewportSize({width:390,height:844});
      assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Reader overflows on mobile');
      await page.getByRole('button',{name:'Contents',exact:true}).click();
      await page.locator('[data-chapter-link="chapter-02"]').click();assert.equal(await page.locator('#contents-button').getAttribute('aria-expanded'),'false');
      await page.screenshot({path:path.join(artifacts,m.id+'-'+edition+'-mobile.png'),fullPage:true,animations:'disabled'});
      await page.emulateMedia({media:'print'});assert.equal(await page.locator('.chapter:visible').count(),m.chapters);assert.match(await page.locator('[data-print-note]').first().innerText(),/Practice notes/);
      await page.emulateMedia({media:'screen'});await page.setViewportSize({width:1440,height:1000});
      console.log('PASS',m.id,edition,'TOC, search, ticks, notes, export/import, mobile, complete print view');
    }
    await context.close();
  }
  const page=await browser.newPage({viewport:{width:1440,height:1000}});page.on('pageerror',e=>errors.push(e.message));
  await page.goto(base+'/START_HERE.html');assert.equal(await page.getByRole('link',{name:'Open this book →'}).count(),2);
  await page.screenshot({path:path.join(artifacts,'library-desktop.png'),fullPage:true,animations:'disabled'});
  for(const m of manifest){const r=await page.request.get(base+'/books/'+m.file.replace('.html','.md'));assert.ok(r.ok());}
  await page.goto(base);await page.getByRole('heading',{name:'Your automation playground.'}).waitFor();assert.equal(await page.getByRole('link',{name:'Guides & checklists',exact:true}).count(),2);
  const config=await (await page.request.get(base+'/api/config')).json();
  // Follow the manual lesson using only the three workplace forms.
  const hvac=config.scenarios.find(s=>s.id==='hvac');
  for(let i=0;i<3;i++){
    await page.goto(base+`/workplace?scenario=hvac&app=${i}`);await page.getByRole('heading',{name:'Create a record',exact:true}).waitFor();
    for(const key of hvac.stage_fields[i])await page.locator('#work-'+key).fill(String(hvac.fields.find(f=>f.key===key).default));
    await page.getByRole('button',{name:'Save to '+hvac.targets[i].name,exact:true}).click();await page.getByRole('heading',{name:'Saved record',exact:true}).waitFor();
    const doc=page.getByRole('link',{name:'Download populated document',exact:true});assert.equal(await doc.count(),1);const r=await page.request.get(base+await doc.getAttribute('href'));assert.ok(r.ok());assert.equal((await r.body()).subarray(0,5).toString(),'%PDF-');
  }
  console.log('PASS full manual HVAC lesson: 32 field entries, 3 saved records and documents');
  await post(page,'/api/reset',{scenario:'hvac'});
  await page.goto(base+'/#scenario/hvac/automate');await page.getByRole('button',{name:'Preview field mapping',exact:true}).click();await page.getByRole('heading',{name:'Mapping preview'}).waitFor();
  await page.getByRole('button',{name:'Populate all three apps',exact:true}).click();await page.getByRole('heading',{name:'Three destinations. Verified.',exact:true}).waitFor();
  await page.getByRole('button',{name:'Complete the visit',exact:true}).click();await apply(page);
  const billing=page.locator('.destination').filter({has:page.getByRole('heading',{name:'Billing Desk',exact:true})});assert.match(await billing.innerText(),/250\.00/);
  await page.getByRole('link',{name:'Automate it',exact:true}).click();await page.locator('#intake-job_ref').fill('JOB-1043');await page.locator('#intake-slot').fill('2026-10-07 10:00');await page.getByRole('button',{name:'Populate all three apps',exact:true}).click();await page.getByRole('heading',{name:'Three destinations. Verified.',exact:true}).waitFor();
  console.log('PASS HVAC automation, completion total, and second job tutorial');
  // The new capacity-change lesson must recover the held check-in without duplicate effects.
  await page.goto(base+'/#scenario/events/automate');await page.locator('#intake-capacity').fill('1');await page.getByRole('button',{name:'Populate all three apps'}).click();await page.getByRole('heading',{name:'Three destinations. Verified.',exact:true}).waitFor();
  await page.getByRole('link',{name:'Automate it',exact:true}).click();for(const [k,v] of Object.entries({registration_ref:'REG-012',full_name:'Taylor Sample',email:'taylor@example.invalid'}))await page.locator('#intake-'+k).fill(v);
  await page.getByRole('button',{name:'Populate all three apps'}).click();await page.getByRole('heading',{name:'Three destinations. Verified.',exact:true}).waitFor();assert.match(await page.locator('.destinations').innerText(),/Waitlisted/);
  await page.getByRole('button',{name:'Check in attendee'}).click();await apply(page,'One handoff needs attention.');
  await page.getByRole('link',{name:'Automate it',exact:true}).click();await page.locator('#intake-capacity').fill('2');await page.getByRole('button',{name:'Populate all three apps'}).click();await page.getByRole('heading',{name:'Three destinations. Verified.',exact:true}).waitFor();
  await page.getByRole('button',{name:'Check in attendee'}).click();await apply(page);assert.equal(await page.locator('.destination .pill').filter({hasText:'Checked in'}).count(),3);
  console.log('PASS event capacity, waitlist hold, deliberate capacity correction, and check-in tutorial');
  assert.deepEqual(errors,[]);
  await fs.writeFile(path.join(artifacts,'result.json'),JSON.stringify({checked_at:new Date().toISOString(),status:'passed',books:manifest,browser_errors:errors,environment:'isolated temporary app databases and browser contexts'},null,2));
  console.log('PASS no browser errors; all practice changes were in isolated temporary stores');
}finally{
  await browser.close();server.kill('SIGINT');await new Promise(resolve=>{if(server.exitCode!==null)resolve();else server.once('exit',resolve);});await fs.rm(temp,{recursive:true,force:true});
}
