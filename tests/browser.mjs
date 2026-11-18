// Program: free_intro - browser.mjs
// Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
// Last Modified: 2026-11-18
// Purpose: Browser smoke test: runs every workflow through the UI, then checks the messy-workbook path and the mobile layout.
import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
// Demo address (overridable with DEMO_URL), a headless browser, and a collector for page errors.
const base=process.env.DEMO_URL||'http://127.0.0.1:8765';
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
const request=async(path,body)=>{const r=await page.request.post(base+path,{data:body});assert.ok(r.ok(),await r.text());return r.json();};
// Overview page, then each workflow: reset, run it, confirm three saved records and six trace steps.
try{
  await page.goto(base);await page.getByRole('heading',{name:'Your automation playground.'}).waitFor();
  await fs.mkdir('/tmp/relayworks-checks',{recursive:true});await page.screenshot({path:'/tmp/relayworks-checks/overview.png',fullPage:true});
  const config=await (await page.request.get(base+'/api/config')).json();
  for(const s of config.scenarios){
    await request('/api/reset',{scenario:s.id});
    await page.goto(`${base}/#scenario/${s.id}/automate`);
    await page.getByRole('button',{name:'Populate all three apps'}).click();
    await page.getByRole('heading',{name:'Three destinations. Verified.'}).waitFor();
    assert.equal(await page.getByRole('link',{name:'Open saved record'}).count(),3);
    await page.getByRole('link',{name:'Under the hood'}).click();
    await page.getByRole('heading',{name:'Actual HTTP traffic'}).waitFor();
    assert.equal(await page.locator('.trace-step').count(),6);
    console.log('PASS browser workflow:',s.id);
  }
  // Messy workbook to mapping to intake preview.
  await page.goto(base+'/#connections');await page.getByRole('heading',{name:'The mess is welcome.'}).waitFor();
  await page.locator('[data-action="fixture"][data-scenario="hvac"]').click();
  await page.getByRole('heading',{name:'After cleanup'}).waitFor();
  await page.getByRole('button',{name:'Use this row in the intake'}).click();
  await page.getByRole('heading',{name:'Enter it once.'}).waitFor();
  assert.equal(await page.locator('#intake-email').inputValue(),'avery@example.invalid');
  assert.equal(await page.locator('#intake-fee').inputValue(),'95');
  await page.getByRole('button',{name:'Preview field mapping'}).click();
  await page.getByRole('heading',{name:'Mapping preview'}).waitFor();
  await page.screenshot({path:'/tmp/relayworks-checks/intake.png',fullPage:true});
  console.log('PASS browser dirty workbook → mapping → intake preview');
  // Mobile layout must not scroll sideways and the navigation must open.
  await page.setViewportSize({width:390,height:844});await page.goto(base);
  await page.getByRole('heading',{name:'Your automation playground.'}).waitFor();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Mobile layout overflows');
  await page.screenshot({path:'/tmp/relayworks-checks/mobile.png',fullPage:true});
  await page.getByRole('button',{name:'Toggle navigation'}).click();await page.locator('.sidebar.open').waitFor();
  console.log('PASS mobile layout and navigation');
  assert.deepEqual(errors,[]);console.log('PASS no browser runtime errors');
}finally{await browser.close();}
