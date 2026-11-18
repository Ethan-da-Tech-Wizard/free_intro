// Program: free_intro - verify_schedule.mjs
// Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
// Last Modified: 2026-11-18
// Purpose: Checks the real recurring-import timer against the public Google Sheet: enables it, waits for its first pull, confirms every row reached all three destination apps, then switches it off.

/** Exercise the actual minimum-interval public Sheet timer, then leave it off. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
// Address of the running demo; override with the DEMO_URL environment variable.
const base=process.env.DEMO_URL||'http://127.0.0.1:8875';
/**
 * Call the demo API (GET without a body, POST with JSON) and return the parsed reply.
 */
async function api(path,body){const r=await fetch(base+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});const data=await r.json();assert.ok(r.ok,JSON.stringify(data));return data;}
// Smallest allowed interval (60 seconds) so the check finishes quickly.
const config={enabled:true,kind:'google',scenario:'events',interval:60};
const start=new Date().toISOString();
// Always disable the timer afterwards (see the finally block), even if a check fails.
try{
  await api('/api/schedules',config);console.log('Timer enabled; verifying its real first scheduled pull.');
  // Wait up to about 100 seconds for the timer's first scheduled pull and its summary message.
  let schedule;
  for(let i=0;i<50;i++){
    await new Promise(resolve=>setTimeout(resolve,2000));schedule=await api('/api/schedules');
    if(schedule.last_run)break;
  }
  assert.ok(schedule.last_run,'Timer did not execute');assert.match(schedule.message,/30 rows submitted/);
  // Wait for the queued runs to finish before counting records.
  let dashboard;
  for(let i=0;i<50;i++){
    dashboard=await api('/api/dashboard');if(!dashboard.runs.some(r=>r.scenario==='events'&&['running','queued'].includes(r.status)))break;
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  // Count the records created from the sheet in each of the three events apps.
  const records=await Promise.all([0,1,2].map(i=>api(`/api/workplaces/events-${i}/records`)));
  const counts=records.map(x=>x.records.filter(r=>r.external_key.startsWith('SHEET-')).length);
  assert.deepEqual(counts,[30,30,30]);
  // Save the evidence of the timer run.
  const proof={started_at:start,verified_at:new Date().toISOString(),schedule,google_rows_saved_in_each_app:counts,waitlisted:records[1].records.filter(r=>r.payload.status==='Waitlisted').length};
  await fs.writeFile('fixtures/public/schedule-verification.json',JSON.stringify(proof,null,2)+'\n');console.log('PASS actual timer → public Google Sheet → 30 rows in each of three workplaces.');
}finally{await api('/api/schedules',{...config,enabled:false});console.log('Timer disabled after verification.');}
