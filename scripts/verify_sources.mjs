import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
const base=process.env.DEMO_URL||'http://127.0.0.1:8765';
const post=async(path,body)=>{const r=await fetch(base+path,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});const data=await r.json();assert.ok(r.ok,JSON.stringify(data));return data;};
await fs.mkdir('fixtures/public',{recursive:true});
const outcomes=[];
for(const [provider,scenario] of [['google','events'],['openf1','sports']]){
  const source=await post('/api/sources/'+provider,{});
  assert.ok(source.rows.length>0);assert.ok(source.http_status===200||source.requests?.every(r=>r.status===200));
  await fs.writeFile(`fixtures/public/${provider}.json`,JSON.stringify(source,null,2)+'\n');
  const mapped=await post('/api/mapping',{source_id:source.id,scenario,row:0});
  const started=await post('/api/runs',{scenario,data:mapped.data,source:mapped.source});
  let run;
  for(let n=0;n<100;n++){run=await (await fetch(base+'/api/runs/'+started.run.id)).json();if(!['queued','running'].includes(run.status))break;await new Promise(r=>setTimeout(r,100));}
  assert.equal(run.status,'complete',run.message);assert.equal(run.outputs.length,3);
  const outcome={provider,scenario,source_id:source.id,source_kind:source.kind,rows:source.rows.length,columns:source.columns,requests:source.requests||[{url:source.request_url,status:source.http_status}],fetched_at:source.fetched_at,run_id:run.id,outputs:run.outputs.map(o=>({app:o.app_id,record_id:o.record.id})),cost:source.cost};
  outcomes.push(outcome);console.log('VERIFIED',JSON.stringify(outcome));
}
await fs.writeFile('fixtures/public/verification.json',JSON.stringify({verified_at:new Date().toISOString(),outcomes},null,2)+'\n');
