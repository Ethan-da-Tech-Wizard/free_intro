// ==============================================================================
// Program: verify_sources.mjs
// Programmer: Ethan-da-Tech-Wizard
// Last Modified: November 18, 2026
// Purpose: Educational automation and workflow orchestration module for free_intro.
//          Provides structured data generation, asset planning, and contracts.
// ==============================================================================

// Important: this script OVERWRITES the recorded provider snapshots in fixtures/public/ with the live
// responses it fetches, so run it only when you intend to refresh the recordings that offline demos replay
// (/api/sources/recorded-google and recorded-openf1 in app/server.py).
// Live check of the two public sources (Google Sheet export and OpenF1): fetch each, run it through the
// workflow, and save the raw responses plus a verification summary under fixtures/public/. Needs network access.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
// Demo server to drive; override with DEMO_URL.
const base=process.env.DEMO_URL||'http://127.0.0.1:8875';
// JSON POST helper that fails on any non-2xx response.
const post=async(path,body)=>{const r=await fetch(base+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await r.json();assert.ok(r.ok,JSON.stringify(data));return data;};
await fs.mkdir('fixtures/public',{recursive:true});
const outcomes=[];
// Provider -> scenario that consumes its data.
for(const [provider,scenario] of [['google','events'],['openf1','sports']]){
  const source=await post('/api/sources/'+provider,{});
  // Expect rows and HTTP 200 (single request, or every request for multi-request providers).
  assert.ok(source.rows.length>0);assert.ok(source.http_status===200||source.requests?.every(r=>r.status===200));
  await fs.writeFile(`fixtures/public/${provider}.json`,JSON.stringify(source,null,2)+'\n');
  // Map the first source row to workflow fields and run it end to end.
  const mapped=await post('/api/mapping',{source_id:source.id,scenario,row:0});
  const started=await post('/api/runs',{scenario,data:mapped.data,source:mapped.source});
  // Poll up to ~10 s for the run to finish.
  let run;
  for(let n=0;n<100;n++){run=await (await fetch(base+'/api/runs/'+started.run.id)).json();if(!['queued','running'].includes(run.status))break;await new Promise(r=>setTimeout(r,100));}
  assert.equal(run.status,'complete',run.message);assert.equal(run.outputs.length,3);
  // Summary of what was fetched and which records were created.
  const outcome={provider,scenario,source_id:source.id,source_kind:source.kind,rows:source.rows.length,columns:source.columns,requests:source.requests||[{url:source.request_url,status:source.http_status}],fetched_at:source.fetched_at,run_id:run.id,outputs:run.outputs.map(o=>({app:o.app_id,record_id:o.record.id})),cost:source.cost};
  outcomes.push(outcome);console.log('VERIFIED',JSON.stringify(outcome));
}
await fs.writeFile('fixtures/public/verification.json',JSON.stringify({verified_at:new Date().toISOString(),outcomes},null,2)+'\n');
