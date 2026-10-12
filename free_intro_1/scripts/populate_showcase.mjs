/** Leave all 24 applications populated after destructive rehearsal/reset lessons. */
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {chromium} from '@playwright/test';
const root=path.resolve(import.meta.dirname,'..'),base='http://127.0.0.1:8875';
const dir=path.join(root,'audit/final-state');await fs.mkdir(dir,{recursive:true});
async function api(route,body){const r=await fetch(base+route,{method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json'},body:body===undefined?undefined:JSON.stringify(body)});const d=await r.json();assert.ok(r.ok,JSON.stringify(d));return d;}
const config=await api('/api/config');assert.equal(config.data_dir,path.join(root,'runtime'));
await api('/api/schedules',{enabled:false,kind:'google',scenario:'events',interval:300});
const report={created_at:new Date().toISOString(),base,scenarios:[],note:'Final arrangement after all documented reset/failure lessons. Records below were saved through actual local APIs, then read back and opened in the browser. Earlier lesson evidence remains in audit/attempts.'};
const inputs=Object.fromEntries(config.scenarios.map(s=>[s.id,Object.fromEntries(s.fields.map(f=>[f.key,f.default]))]));
async function run(id,data,kind='intake',action,event_id,source={kind:'final rehearsal presentation fixture'}){
 const response=await api('/api/runs',{scenario:id,data,kind,action,event_id,source});let result;
 for(let n=0;n<200;n++){result=await api('/api/runs/'+response.run.id);if(!['queued','running'].includes(result.status))break;await new Promise(r=>setTimeout(r,60));}
 assert.equal(result.status,'complete',result.message);assert.equal(result.outputs.length,3);await fs.writeFile(path.join(dir,'run-'+result.id+'.json'),JSON.stringify(result,null,2));return result;
}
const verified=JSON.parse(await fs.readFile(path.join(root,'fixtures/public/verification.json'),'utf8'));
for(const s of config.scenarios){
 await api('/api/reset',{scenario:s.id});for(const t of s.targets)await api('/api/workplaces/'+t.id+'/settings',{online:true,authorized:true});
 let data=inputs[s.id],result,source;
 if(s.id==='sports'){
  const sourceId=verified.outcomes.find(o=>o.provider==='openf1').source_id;const mapped=await api('/api/mapping',{source_id:sourceId,scenario:s.id,row:0});data=mapped.data;source=mapped.source;
 }
 if(s.id==='events'){
  const sourceId=verified.outcomes.find(o=>o.provider==='google').source_id;const source=await api('/api/sources/'+sourceId);
  for(let i=0;i<source.rows.length;i++){const mapped=await api('/api/mapping',{source_id:sourceId,scenario:s.id,row:i});await run(s.id,mapped.data,'intake',undefined,undefined,mapped.source);}
 }
 result=await run(s.id,data,'intake',undefined,undefined,source);
 if(s.id==='hvac'){
  result=await run(s.id,data,'completion',{hours:1.5,hourly_rate:80,parts:35},'completion-'+data.job_ref);
  data={...data,job_ref:'JOB-1043',slot:'2026-10-07 10:00'};await run(s.id,data);
  result=await run(s.id,data,'completion',{hours:1.5,hourly_rate:80,parts:35},'completion-'+data.job_ref);
  assert.equal(result.outputs[2].record.payload.total_usd,'250.00');
 }
 if(s.id==='legal'){data={...data,matter_ref:'MAT-0204-REVIEW',other_party:'Existing demo client',_review_confirmed:true};result=await run(s.id,data);}
 if(s.id==='clinic'){data={...data,patient_ref:'PAT-0310-B',full_name:'Another Sample',slot:'2026-10-08 12:00'};result=await run(s.id,data);}
 if(s.id==='retail'){data={...data,receipt_ref:'REC-089'};result=await run(s.id,data);assert.equal(result.outputs[1].record.payload.stock_quantity,24);assert.equal(result.outputs[2].record.payload.available_quantity,22);}
 if(s.id==='reseller'){result=await run(s.id,data,'sale',{buyer:'Taylor Example',ship_to:'10 Example Terrace',sale_ref:'SALE-019'},'sale-'+data.sku);assert.equal(result.outputs[0].record.payload.stock_quantity,0);}
 if(s.id==='property'){result=await run(s.id,data,'invoice',{invoice_ref:'INV-080',job_reference:'FIX-016',invoice_total:180},'invoice-'+data.ticket_ref);}
 if(s.id==='events'){data={...data,registration_ref:'REG-012',full_name:'Taylor Sample',email:'taylor@example.invalid',capacity:2};await run(s.id,data);result=await run(s.id,data,'checkin',{},'checkin-'+data.registration_ref);}
 const apps=[];
 for(const t of s.targets){const records=await api('/api/workplaces/'+t.id+'/records');assert.ok(records.records.length);const r=result.outputs.find(o=>o.app_id===t.id).record;
  const csv=await fetch(base+'/api/workplaces/'+t.id+'/export.csv');assert.ok(csv.ok);await fs.writeFile(path.join(dir,t.id+'.csv'),Buffer.from(await csv.arrayBuffer()));
  const pdf=await fetch(base+`/api/workplaces/${t.id}/document.pdf/${r.id}`);assert.ok(pdf.ok);await fs.writeFile(path.join(dir,t.id+'.pdf'),Buffer.from(await pdf.arrayBuffer()));
  apps.push({id:t.id,name:t.name,count:records.records.length,status:r.payload.status,record_id:r.id,url:`/workplace?scenario=${s.id}&app=${t.index}&record=${r.id}`,records:records.records});
 }
 report.scenarios.push({id:s.id,name:s.short,company:s.company,run_id:result.id,source:result.source,apps});console.log('POPULATED',s.id,apps.map(a=>a.count).join('/'));
}
const browser=await chromium.launch({headless:true});
try{
 const p=await browser.newPage({viewport:{width:1440,height:1000}});
 for(const s of report.scenarios){
  await p.goto(base+'/#scenario/'+s.id+'/results');await p.getByRole('heading',{name:'Three destinations. Verified.',exact:true}).waitFor();
  await p.screenshot({path:path.join(dir,s.id+'-results.png'),fullPage:true});
  for(const a of s.apps){await p.goto(base+a.url);await p.getByRole('heading',{name:'Saved record',exact:true}).waitFor();await p.screenshot({path:path.join(dir,a.id+'.png'),fullPage:true});}
 }
}finally{await browser.close();}
report.dashboard=await api('/api/dashboard');report.schedule=await api('/api/schedules');assert.equal(report.schedule.enabled,false);report.record_count=report.scenarios.flatMap(s=>s.apps).reduce((n,a)=>n+a.count,0);report.finished_at=new Date().toISOString();
await fs.writeFile(path.join(dir,'manifest.json'),JSON.stringify(report,null,2)+'\n');console.log('PASS all 24 apps visible;',report.record_count,'records; all latest workflows complete; timer off.');
