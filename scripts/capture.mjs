/** Actual browser evidence. This resets only the owned local demonstration stores. */
import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import crypto from 'node:crypto';
const base=process.env.DEMO_URL||'http://127.0.0.1:8765';
const viewport={width:1440,height:1050};
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport});
const failures=[];page.on('pageerror',error=>failures.push(error.message));
const manifest={captured_at:new Date().toISOString(),fixture_revision:'demonstration-contract-1',note:'Actual Playwright browser interactions. Manual typing is scripted to make the comparison repeatable, not measured human performance. Local workplaces and people are synthetic. External source captures carry provenance.',captures:[]};
await fs.mkdir('evidence',{recursive:true});
const get=async path=>{const r=await page.request.get(base+path);assert.ok(r.ok(),await r.text());return r.json();};
const post=async(path,body)=>{const r=await page.request.post(base+path,{data:body});assert.ok(r.ok(),await r.text());return r.json();};
async function go(path,heading){await page.goto(base+path);await page.getByRole('heading',{name:heading,exact:true}).first().waitFor();}
async function shot(s,step,label,mode='automated',run=null,record=null,sourceKind='synthetic demo fixture'){
  await page.evaluate(()=>{document.activeElement?.blur();window.scrollTo(0,0);document.getElementById('toast')?.classList.remove('visible');});
  await page.evaluate(()=>new Promise(r=>requestAnimationFrame(()=>requestAnimationFrame(r))));
  const path=`evidence/${s.id}-${step}.png`;
  const blob=await page.screenshot({path,fullPage:true,animations:'disabled'});
  manifest.captures.push({scenario_id:s.id,fixture_revision:manifest.fixture_revision,run_id:run?.id||null,mode,step_id:step,label,captured_at:new Date().toISOString(),app_url:page.url(),target_record_id:record,source_kind:sourceKind,viewport,path,sha256:crypto.createHash('sha256').update(blob).digest('hex')});
}
async function waitRun(id,status='complete'){
  for(let n=0;n<100;n++){const r=await get('/api/runs/'+id);if(!['queued','running'].includes(r.status)){assert.equal(r.status,status,r.message);return r;}await new Promise(r=>setTimeout(r,60));}
  throw new Error('Run timed out.');
}
async function runAt(s,tab='results'){
  const dashboard=await get('/api/dashboard');const summary=dashboard.runs.find(r=>r.scenario===s.id&&r.status!=='archived');
  assert.ok(summary);const run=await waitRun(summary.id);await go(`/#scenario/${s.id}/${tab}`,tab==='technical'?'Actual HTTP traffic':s.short);await page.getByRole('heading',{name:'Three destinations. Verified.',exact:true}).waitFor();return run;
}
async function fillManual(s,i){
  await go(`/workplace?scenario=${s.id}&app=${i}`,'Create a record');
  for(const key of s.stage_fields[i])await page.locator('#work-'+key).fill(String(s.fields.find(f=>f.key===key).default));
  await shot(s,`0${i+2}-manual-app-${i+1}`,`Manual · enter fields in ${s.targets[i].name}`,'manual');
  await page.getByRole('button',{name:'Save to '+s.targets[i].name,exact:true}).click();
  await page.getByRole('heading',{name:'Saved record',exact:true}).waitFor();
  const record=new URL(page.url()).searchParams.get('record');assert.ok(record);
  await shot(s,`0${i+2}b-manual-saved-${i+1}`,`Manual · saved ${s.targets[i].name}`,'manual',null,record);
}
try{
  const config=await get('/api/config');
  if(process.argv.includes('--refresh-technical')){
    const existing=JSON.parse(await fs.readFile('evidence/manifest.json','utf8'));
    for(const c of existing.captures.filter(c=>c.step_id==='09-technical-trace')){
      await go('/#history','Every handoff has a history.');
      await page.locator(`[data-action="inspect-run"][data-run="${c.run_id}"]`).click();
      await page.getByRole('heading',{name:'Actual HTTP traffic',exact:true}).waitFor();
      await page.locator('.trace-step').first().locator('summary').click();
      await page.evaluate(()=>{document.activeElement?.blur();window.scrollTo(0,0);});
      const blob=await page.screenshot({path:c.path,fullPage:true,animations:'disabled'});
      c.captured_at=new Date().toISOString();c.sha256=crypto.createHash('sha256').update(blob).digest('hex');
    }
    existing.technical_refreshed_at=new Date().toISOString();
    await fs.writeFile('evidence/manifest.json',JSON.stringify(existing,null,2)+'\n');
    assert.deepEqual(failures,[]);console.log('Refreshed eight technical captures from their original retained runs.');
  }else{
  await post('/api/schedules',{enabled:false,kind:'google',scenario:'events',interval:300});
  for(const s of config.scenarios){
    await post('/api/reset',{scenario:s.id});
    await go(`/#scenario/${s.id}/manual`,s.short);await shot(s,'01-source','Source paperwork · the same facts for both paths','source');
    for(let i=0;i<3;i++)await fillManual(s,i);
    await post('/api/reset',{scenario:s.id});
    await go(`/#scenario/${s.id}/automate`,'Enter it once.');
    await page.getByRole('button',{name:'Preview field mapping'}).click();await page.getByRole('heading',{name:'Mapping preview'}).waitFor();
    await shot(s,'05-automation-review','After · one reviewed intake for all three apps','review');
    await page.getByRole('button',{name:'Populate all three apps'}).click();
    await page.getByRole('heading',{name:'Three destinations. Verified.',exact:true}).waitFor();
    const run=await runAt(s);
    for(let i=0;i<3;i++){
      const record=run.outputs[i].record.id;
      await go(`/workplace?scenario=${s.id}&app=${i}&record=${record}`,'Saved record');
      await shot(s,`0${i+6}-after-app-${i+1}`,`After · ${s.targets[i].name} populated automatically`,'automated',run,record);
      const document=await page.request.get(base+`/api/workplaces/${s.targets[i].id}/document.pdf/${record}`);
      assert.ok(document.ok());assert.ok((await document.body()).subarray(0,5).equals(Buffer.from('%PDF-')));
    }
    await go(`/#scenario/${s.id}/technical`,'Actual HTTP traffic');
    await page.locator('.trace-step').first().locator('summary').click();await shot(s,'09-technical-trace','Proof · actual request and destination read-back','technical',run);
    // Every workflow demonstrates a real 403/503 handoff and a resumed, verified job.
    const failureKey=s.id==='hvac'?'authorized':'online',failTarget=s.targets[2];
    await page.locator(`[data-action="setting"][data-app="${failTarget.id}"][data-key="${failureKey}"]`).click();
    const input=Object.fromEntries(s.fields.map(f=>[f.key,f.default]));input[s.primary]+='-RECOVERY';
    if(s.id==='hvac'){input.slot='2026-10-12 15:00';input.customer_ref='C-RECOVERY';}
    if(s.id==='clinic')input.slot='2026-10-12 16:00';
    const pending=await post('/api/runs',{scenario:s.id,data:input,source:{kind:'synthetic failure and recovery demonstration'}});
    const failed=await waitRun(pending.run.id,'needs_attention');
    await page.reload();await page.getByRole('heading',{name:'One handoff needs attention.',exact:true}).waitFor();
    await shot(s,'10-failure','Exception · destination denies or cannot accept the request','failure',failed);
    await page.locator(`[data-action="setting"][data-app="${failTarget.id}"][data-key="${failureKey}"]`).click();
    await page.getByRole('button',{name:'Resume from saved step'}).click();
    await page.getByRole('heading',{name:'Three destinations. Verified.',exact:true}).waitFor();
    const recovered=await get('/api/runs/'+failed.id);assert.equal(recovered.outputs.length,3);
    assert.ok(recovered.steps.some(r=>r.status===403||r.status===503));
    await shot(s,'11-recovered','Recovery · completed steps retained, failed transfer resumed','recovery',recovered);
    // Additional domain-specific exception evidence.
    if(s.id==='legal'){
      await go('/#scenario/legal/results','Law office');await page.getByRole('button',{name:s.action_label}).click();
      await page.getByRole('button',{name:'Preview field mapping'}).click();await page.locator('#form-error [role="alert"]').waitFor();
      await shot(s,'12-review-hold','Legal intake · possible party match held for review','review');
      await page.locator('#review-confirmed').check();await page.getByRole('button',{name:'Populate all three apps'}).click();await page.getByRole('heading',{name:'Three destinations. Verified.',exact:true}).waitFor();
      await shot(s,'13-review-approved','Legal intake · reviewer decision recorded','recovery',await runAt(s));
    }
    if(s.id==='clinic'){
      await go('/#scenario/clinic/results',s.short);await page.getByRole('button',{name:s.action_label}).click();await page.getByRole('heading',{name:'One handoff needs attention.',exact:true}).waitFor();
      await shot(s,'12-conflict','Clinic · duplicate appointment slot rejected','failure');
      await page.getByRole('link',{name:'Automate it',exact:true}).click();await page.locator('#intake-slot').fill('2026-10-13 16:00');await page.getByRole('button',{name:'Populate all three apps'}).click();await page.getByRole('heading',{name:'Three destinations. Verified.',exact:true}).waitFor();
      await shot(s,'13-conflict-resolved','Clinic · corrected slot creates the appointment','recovery',await runAt(s));
    }
    if(s.id==='hvac'||s.id==='reseller'||s.id==='property'||s.id==='events'){
      await go(`/#scenario/${s.id}/results`,s.short);await page.getByRole('button',{name:s.action_label}).click();
      await page.getByRole('button',{name:'Apply and verify'}).click();await page.getByRole('heading',{name:'Three destinations. Verified.',exact:true}).waitFor();
      await shot(s,'12-business-followup',s.action_label+' · verified updated records','follow-up',await runAt(s));
    }
    const ugly=await post('/api/sources/fixture',{scenario:s.id});
    await go(`/#source/${ugly.id}/${s.id}`,s.company+' · messy workbook');await shot(s,'14-ugly-workbook','Original mess → cleaned values → explicit field mapping','source',null,null,ugly.kind);
    await fs.writeFile('evidence/manifest.json',JSON.stringify(manifest,null,2)+'\n');
    console.log('CAPTURED',s.id,manifest.captures.filter(c=>c.scenario_id===s.id).length,'screenshots');
  }
  // The externally fetched source pages show provider URLs, HTTP status and timestamps.
  const verified=JSON.parse(await fs.readFile('fixtures/public/verification.json','utf8'));
  for(const item of verified.outcomes){
    const s=config.scenarios.find(s=>s.id===item.scenario),source=await get('/api/sources/'+item.source_id);
    await go(`/#source/${item.source_id}/${s.id}`,source.name);await shot(s,'15-public-source',item.provider==='google'?'Real Google Sheet · 30 rows fetched without an API key':'Real OpenF1 data · driver, session, and lap requests','live-source',null,null,item.source_kind);
    await page.getByRole('button',{name:'Use this row in the intake'}).click();await page.getByRole('heading',{name:'Enter it once.'}).waitFor();await shot(s,'16-public-intake','Public source values mapped into the workplace intake','review',null,null,item.source_kind);
    await page.getByRole('button',{name:'Populate all three apps'}).click();await page.getByRole('heading',{name:'Three destinations. Verified.',exact:true}).waitFor();
    await shot(s,'17-public-populated','Real source data saved into three local workplaces','automated',await runAt(s),null,item.source_kind);
  }
  await fs.writeFile('evidence/manifest.json',JSON.stringify(manifest,null,2)+'\n');
  await go('/','Your automation playground.');await page.evaluate(()=>window.scrollTo(0,0));await page.screenshot({path:'evidence/showcase-overview.png',fullPage:true});
  assert.deepEqual(failures,[]);console.log('COMPLETE',manifest.captures.length,'actual screenshots, no browser errors.');
  }
}finally{await browser.close();}
