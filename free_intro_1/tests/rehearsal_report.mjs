/** Read-only verification of the delivered report, evidence links, and final saved state. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {execFileSync} from 'node:child_process';
import {chromium,expect} from '@playwright/test';

const root=path.resolve(import.meta.dirname,'..'),base='http://127.0.0.1:8875';
const out=path.join(root,'audit/report-verification');await fs.mkdir(out,{recursive:true});
await fs.writeFile(path.join(out,'result.json'),JSON.stringify({status:'running',started_at:new Date().toISOString()})+'\n');
const final=JSON.parse(await fs.readFile(path.join(root,'audit/final-state/manifest.json'),'utf8'));
const checks=JSON.parse(await fs.readFile(path.join(root,'audit/checklist-coverage.json'),'utf8'));
const summary=JSON.parse(await fs.readFile(path.join(root,'audit/summary.json'),'utf8'));
const errors=[],steps=[];let linkCount=0;
function pass(message){steps.push(message);console.log('PASS',message);}
async function get(url){const r=await fetch(url);assert.ok(r.ok,`${r.status} ${url}`);return r.json();}
async function capture(page,name){
 await page.evaluate(async()=>{await document.fonts.ready;await new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r)));});
 await page.screenshot({path:path.join(out,name),fullPage:true,animations:'disabled'});
}
assert.equal((await get(base+'/api/config')).data_dir,path.join(root,'runtime'));
for(const scenario of final.scenarios){
 for(const app of scenario.apps){
  const actual=(await get(base+'/api/workplaces/'+app.id+'/records')).records;
  assert.deepEqual(actual,app.records,app.id+' retained exact final records after restart');
  const pdf=execFileSync('pdftotext',[path.join(root,'audit/final-state',app.id+'.pdf'),'-'],{encoding:'utf8'});
  assert.ok(pdf.includes(app.record_id),app.id+' PDF has its actual saved reference');
 }
}
assert.equal((await get(base+'/api/schedules')).enabled,false);
pass('All 24 workplace stores retain the exact 126 final records; each PDF identifies its saved record; timer off.');

const browser=await chromium.launch({headless:true});
try{
 for(const mode of ['file','http']){
  const context=await browser.newContext({viewport:{width:1440,height:1050},acceptDownloads:true});
  const page=await context.newPage();page.on('pageerror',e=>errors.push(e.message));
  await page.goto(mode==='file'?pathToFileURL(path.join(root,'AUDIT.html')).href:base+'/AUDIT.html');
  assert.equal(await page.locator('.business-card').count(),8);
  assert.equal(await page.locator('.business-card li').count(),24);
  await capture(page,mode+'-results.png');
  if(mode==='http'){
   const links=await page.locator('a[href]').evaluateAll(nodes=>[...new Set(nodes.map(n=>n.getAttribute('href')))]);
   for(const href of links){
    const url=new URL(href,base+'/AUDIT.html');
    if(url.origin!==base||url.pathname==='/workplace'||url.pathname==='/')continue;
    const file=path.join(root,decodeURIComponent(url.pathname));
    assert.equal((await fs.stat(file)).isFile(),true,href);linkCount++;
   }
   for(const url of ['/AUDIT.html','/web/audit.js','/audit/report-data.js','/audit/summary.json','/audit/live-sources.json','/audit/FINDINGS.md','/audit/OWNER_REHEARSAL.md','/audit/final-state/hvac-2.pdf','/audit/final-state/hvac-2.csv','/audit/final-state/hvac-2.png','/books/THE_WORKS.pdf','/books/BUSINESS_PLAYBOOK.pdf']){
    const r=await page.request.get(base+url);assert.ok(r.ok(),url);await r.dispose();
   }
   pass('Every report file link exists; report scripts, findings, sources, screenshots, CSV and PDF editions are served successfully.');
  }
  await page.getByRole('link',{name:'Watch the steps',exact:true}).click();
  await expect(page.locator('#frame-counter')).toHaveText('1 / '+summary.frames);
  await page.locator('#frame-image').evaluate(img=>img.decode());
  await page.getByRole('button',{name:'Next',exact:true}).click();
  await expect(page.locator('#frame-counter')).toHaveText('2 / '+summary.frames);
  await page.getByRole('button',{name:'Previous',exact:true}).click();
  await page.getByRole('button',{name:'Play screenshots',exact:true}).click();
  await page.waitForFunction(()=>document.querySelector('#frame-counter').textContent.startsWith('2 /'));
  await page.getByRole('button',{name:'Pause',exact:true}).click();
  await page.locator('#frame-slider').fill(String(summary.frames-1));
  assert.equal(await page.locator('#frame-counter').innerText(),summary.frames+' / '+summary.frames);
  await page.locator('#frame-image').evaluate(img=>img.decode());
  await capture(page,mode+'-replay.png');
  const frames=await page.evaluate(()=>window.REHEARSAL_FRAMES);
  for(const frame of frames)assert.equal((await fs.stat(path.join(root,frame.url))).isFile(),true,frame.url);
  await page.getByRole('link',{name:'Action journal',exact:true}).click();
  await page.locator('#journal').waitFor({state:'visible'});
  assert.equal(await page.locator('.exercise').count(),summary.browser_exercises_passed+summary.prior_harness_attempts_failed);
  await page.locator('#action-search').fill('OCR');assert.ok(await page.locator('.exercise:visible').count()>0);
  await page.locator('.exercise:visible summary').first().click();
  await page.getByRole('link',{name:'Every checklist item',exact:true}).click();
  await page.locator('#checklist').waitFor({state:'visible'});
  assert.equal(await page.locator('.check-item:visible').count(),360);
  await page.locator('#book-filter').selectOption('all');assert.equal(await page.locator('.check-item:visible').count(),612);
  await page.locator('#status-filter').selectOption('native');
  assert.equal(await page.locator('.check-item:visible').count(),checks.filter(c=>c.status==='native').length);
  await page.locator('#book-filter').selectOption('business');await page.locator('#status-filter').selectOption('human');
  assert.equal(await page.locator('.check-item:visible').count(),checks.filter(c=>c.book==='business'&&c.status==='human').length);
  await page.locator('#book-filter').selectOption('all');await page.locator('#status-filter').selectOption('all');
  await page.locator('#check-search').fill('middle dot');assert.ok(await page.locator('.check-item:visible').count()>0);
  await page.locator('#check-search').fill('');
  await page.setViewportSize({width:390,height:844});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Report checklist overflows mobile');
  await page.getByRole('link',{name:'Findings & limits',exact:true}).click();
  await page.locator('#findings').waitFor({state:'visible'});
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Report findings overflow mobile');
  await capture(page,mode+'-mobile.png');
  await page.setViewportSize({width:1440,height:1050});
  for(const [book,stem] of [['works','THE_WORKS'],['business','BUSINESS_PLAYBOOK']]){
   await page.goto(mode==='file'?pathToFileURL(path.join(root,stem+'.html')).href:base+'/'+stem+'.html');
   const ids=await page.locator('[data-task]').evaluateAll(nodes=>nodes.map(n=>n.dataset.task));
   const expected=checks.filter(c=>c.book===book);assert.deepEqual(ids,expected.map(c=>c.id));
   await page.locator('#import-file').setInputFiles(path.join(root,'audit',book+'-verified-progress.json'));
   await page.getByRole('status').filter({hasText:'Progress imported.'}).waitFor();
   const checked=expected.filter(c=>['exercised','reviewed'].includes(c.status)).length;
   assert.equal(await page.locator('[data-task]:checked').count(),checked);
   await page.reload();assert.equal(await page.locator('[data-task]:checked').count(),checked);
   assert.equal(await page.getByRole('link',{name:'Rehearsal findings & evidence ↗'}).count(),1);
   const pdf=execFileSync('pdftotext',[path.join(root,'books',stem+'.pdf'),'-'],{encoding:'utf8'});
   if(book==='works')assert.ok(pdf.includes('/home/ethan/pg/free_intro/free_intro_1'));
   assert.ok(pdf.includes(book==='works'?'The Works':'The Business Owner Playbook'));
   assert.ok(pdf.includes('Book complete:'));
  }
  pass(mode+' report: replay/play/pause/slider, journal search, exact 612 checklist IDs, status filters, mobile, and both observed-progress imports/persistence passed.');
  await context.close();
 }
 const page=await browser.newPage();page.on('pageerror',e=>errors.push(e.message));
 await page.goto(base+'/');await page.getByRole('heading',{name:'Your automation playground.'}).waitFor();
 assert.equal(await page.getByRole('link',{name:'Rehearsal findings',exact:true}).count(),1);
 await page.goto(base+'/START_HERE.html');assert.equal(await page.getByRole('link',{name:'findings and recorded walkthrough ↗',exact:true}).count(),1);
 assert.deepEqual(errors,[]);
 pass('Live app and library lead to the report; no browser JavaScript errors.');
 await fs.writeFile(path.join(out,'result.json'),JSON.stringify({status:'passed',checked_at:new Date().toISOString(),steps,link_files_verified:linkCount,browser_errors:errors,records:final.record_count,workplace_apps:24,summary},null,2)+'\n');
}catch(error){
 await fs.writeFile(path.join(out,'result.json'),JSON.stringify({status:'failed',checked_at:new Date().toISOString(),steps,error:error.stack,browser_errors:errors},null,2)+'\n');
 throw error;
}finally{await browser.close();}
