/** Produce blank, standalone PDF editions; no demo data is changed. */
import {chromium} from '@playwright/test';
import {pathToFileURL} from 'node:url';
import path from 'node:path';
import fs from 'node:fs/promises';
const root=path.resolve(import.meta.dirname,'..');
const browser=await chromium.launch({headless:true});
try{
  for(const name of ['THE_WORKS','BUSINESS_PLAYBOOK']){
    const context=await browser.newContext();const page=await context.newPage();
    await page.goto(pathToFileURL(path.join(root,name+'.html')).href);
    await page.emulateMedia({media:'print'});
    await page.evaluate(async()=>{
      document.querySelectorAll('img').forEach(img=>img.loading='eager');
      await Promise.all([...document.images].map(img=>img.decode()));
      await document.fonts.ready;
    });
    const target=path.join(root,'books',name+'.pdf');
    await page.pdf({path:target,format:'A4',preferCSSPageSize:true,printBackground:true,displayHeaderFooter:true,
      headerTemplate:'<span></span>',footerTemplate:`<div style="width:100%;font:9px Arial;color:#647467;padding:0 16mm;display:flex;justify-content:space-between"><span>Relayworks · ${name==='THE_WORKS'?'The Works':'Business Owner Playbook'}</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>`});
    console.log(name+'.pdf', (await fs.stat(target)).size+' bytes');await context.close();
  }
}finally{await browser.close();}
