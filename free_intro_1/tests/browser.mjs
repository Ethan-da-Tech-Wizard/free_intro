// Program: free_intro - browser.mjs
// Programmer: Ethan-da-Tech-Wizard (written with Claude, an AI assistant)
// Last Modified: 2026-11-18
// Purpose: Browser smoke test for the running demo: walks every scenario, imports a messy workbook, checks the mobile layout, and fails on any page error.

import {chromium} from '@playwright/test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
// Address of the running demo; override with the DEMO_URL environment variable.
const base=process.env.DEMO_URL||'http://127.0.0.1:8875';
// Desktop-sized headless browser; page errors are collected for the final check.
const browser=await chromium.launch({headless:true});
const page=await browser.newPage({viewport:{width:1440,height:1000}});
const errors=[];page.on('pageerror',e=>errors.push(e.message));
// POST JSON through the browser's request context, failing on an error status.
const request=async(path,body)=>{const r=await page.request.post(base+path,{data:body});assert.ok(r.ok(),await r.text());return r.json();};
// Overview page loads (screenshot saved to a temporary folder).
try{
  await page.goto(base);await page.getByRole('heading',{name:'Your automation playground.'}).waitFor();
  await fs.mkdir('/tmp/relayworks-checks',{recursive:true});await page.screenshot({path:'/tmp/relayworks-checks/overview.png',fullPage:true});
  const config=await (await page.request.get(base+'/api/config')).json();
  // Each scenario: reset, fill the intake, populate all three apps, then check three saved-record links and six HTTP trace steps.
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
  // Messy workbook flow: import it, use the cleaned row, check the values and preview the mapping.
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
  // Phone-sized screen: the page must not scroll sideways and the menu must open.
  await page.setViewportSize({width:390,height:844});await page.goto(base);
  await page.getByRole('heading',{name:'Your automation playground.'}).waitFor();
  assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth+1),'Mobile layout overflows');
  await page.screenshot({path:'/tmp/relayworks-checks/mobile.png',fullPage:true});
  await page.getByRole('button',{name:'Toggle navigation'}).click();await page.locator('.sidebar.open').waitFor();
  console.log('PASS mobile layout and navigation');
  // No JavaScript errors may have occurred.
  assert.deepEqual(errors,[]);console.log('PASS no browser runtime errors');
}finally{await browser.close();}
