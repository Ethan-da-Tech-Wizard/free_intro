/** Exercise the actual minimum-interval public Sheet timer, then leave it off. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const base=process.env.DEMO_URL||'http://127.0.0.1:8765';
async function api(path,body){const r=await fetch(base+path,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});const data=await r.json();assert.ok(r.ok,JSON.stringify(data));return data;}
const config={enabled:true,kind:'google',scenario:'events',interval:60};
const start=new Date().toISOString();
try{
  await api('/api/schedules',config);console.log('Timer enabled; verifying its real first scheduled pull.');
  let schedule;
  for(let i=0;i<50;i++){
    await new Promise(resolve=>setTimeout(resolve,2000));schedule=await api('/api/schedules');
    if(schedule.last_run)break;
  }
  assert.ok(schedule.last_run,'Timer did not execute');assert.match(schedule.message,/30 rows submitted/);
  let dashboard;
  for(let i=0;i<50;i++){
    dashboard=await api('/api/dashboard');if(!dashboard.runs.some(r=>r.scenario==='events'&&['running','queued'].includes(r.status)))break;
    await new Promise(resolve=>setTimeout(resolve,100));
  }
  const records=await Promise.all([0,1,2].map(i=>api(`/api/workplaces/events-${i}/records`)));
  const counts=records.map(x=>x.records.filter(r=>r.external_key.startsWith('SHEET-')).length);
  assert.deepEqual(counts,[30,30,30]);
  const proof={started_at:start,verified_at:new Date().toISOString(),schedule,google_rows_saved_in_each_app:counts,waitlisted:records[1].records.filter(r=>r.payload.status==='Waitlisted').length};
  await fs.writeFile('fixtures/public/schedule-verification.json',JSON.stringify(proof,null,2)+'\n');console.log('PASS actual timer → public Google Sheet → 30 rows in each of three workplaces.');
}finally{await api('/api/schedules',{...config,enabled:false});console.log('Timer disabled after verification.');}
