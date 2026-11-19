// ==============================================================================
// Program: browser.mjs
// Programmer: Ethan-da-Tech-Wizard
// Last Modified: November 18, 2026
// Purpose: Educational automation and workflow orchestration module for free_intro.
//          Provides structured data generation, asset planning, and contracts.
// ==============================================================================

// How this file fits the app: the browser smoke test (npm run test:browser). With the server already
// running it opens every scenario in real Chromium, resets it, clicks "Populate all three apps" and checks
// the results page (three saved-record links, six trace steps) and that no JavaScript page errors
// occurred. Unlike tests/books.mjs it does not start its own server and it modifies the demo data, so use
// a throw-away instance (python3 app/server.py --data-dir /tmp/relay-demo).
// Smoke test of the live UI in a real browser. It RESETS and re-runs every scenario on the server at
// DEMO_URL, so point it at a disposable demo; screenshots go to /tmp/relayworks-checks.
import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
// Demo server to test; override with DEMO_URL.
const base=process.env.DEMO_URL||'http://127.0.0.1:8875';
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
// JSON POST helper; fails on any non-2xx response.
const request=async(path,body)=>{const r=await page.request.post(base+path,{data:body});assert.ok(r.ok(),await r.text());return r.json();};
try{
  await page.goto(base);await page.getByRole('heading',{name:'Your automation playground.'}).waitFor();
  await fs.mkdir('/tmp/relayworks-checks',{recursive:true});await page.screenshot({path:'/tmp/relayworks-checks/overview.png',fullPage:true});
  const config=await (await page.request.get(base+'/api/config')).json();
  // Each scenario: reset, populate all three apps, expect 3 saved-record links and 6 trace steps (POST + GET per app).
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
  // Messy workbook path: load fixture, use the first row, and verify cleaned values reach the intake form.
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
  // Mobile layout: no horizontal overflow and the navigation toggle works.
  await page.setViewportSize({width:390,height:844});await page.goto(base);
  await page.getByRole('heading',{name:'Your automation playground.'}).waitFor();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Mobile layout overflows');
  await page.screenshot({path:'/tmp/relayworks-checks/mobile.png',fullPage:true});
  await page.getByRole('button',{name:'Toggle navigation'}).click();await page.locator('.sidebar.open').waitFor();
  console.log('PASS mobile layout and navigation');
  assert.deepEqual(errors,[]);console.log('PASS no browser runtime errors');
}finally{await browser.close();}
