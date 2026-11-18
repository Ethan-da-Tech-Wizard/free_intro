// Program: free_intro - verify_schedule.mjs
// Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
// Last Modified: 2026-11-18
// Purpose: Turns on the scheduled public-sheet refresh, confirms it really ran and saved rows in all three apps, saves proof, and turns the schedule off.
/** Exercise the actual minimum-interval public Sheet timer, then leave it off. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
// Demo address (overridable with DEMO_URL) and a small helper that GETs or POSTs JSON to it.
const base=process.env.DEMO_URL||'http://127.0.0.1:8765';
async function api(path,body){const r=await fetch(base+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});const data=await r.json();assert.ok(r.ok,JSON.stringify(data));return data;}
// Schedule settings: public sheet source, events workflow, shortest allowed interval (60 seconds).
const config={enabled:true,kind:'google',scenario:'events',interval:60};
const start=new Date().toISOString();
// Enable the schedule and wait for its first pull (up to about 100 seconds).
try{
  await api('/api/schedules',config);console.log('Timer enabled; verifying its real first scheduled pull.');
  let schedule;
  for(let i=0;i<50;i++){
    await new Promise(resolve=>setTimeout(resolve,2000));schedule=await api('/api/schedules');
    if(schedule.last_run)break;
  }
  assert.ok(schedule.last_run,'Timer did not execute');assert.match(schedule.message,/30 rows submitted/);
  // Wait for the queued runs to finish, then count the saved rows in each app.
  let dashboard;
  for(let i=0;i<50;i++){
    dashboard=await api('/api/dashboard');if(!dashboard.runs.some(r=>r.scenario==='events'&&['running','queued'].includes(r.status)))break;
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  const records=await Promise.all([0,1,2].map(i=>api(`/api/workplaces/events-${i}/records`)));
  const counts=records.map(x=>x.records.filter(r=>r.external_key.startsWith('SHEET-')).length);
  assert.deepEqual(counts,[30,30,30]);
  // Save the evidence to a file.
  const proof={started_at:start,verified_at:new Date().toISOString(),schedule,google_rows_saved_in_each_app:counts,waitlisted:records[1].records.filter(r=>r.payload.status==='Waitlisted').length};
  await fs.writeFile('fixtures/public/schedule-verification.json',JSON.stringify(proof,null,2)+'\n');console.log('PASS actual timer → public Google Sheet → 30 rows in each of three workplaces.');
// Always switch the schedule back off.
}finally{await api('/api/schedules',{...config,enabled:false});console.log('Timer disabled after verification.');}
