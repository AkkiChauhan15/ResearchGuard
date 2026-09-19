/* PLAYWRIGHT_PATH can point to an existing playwright-core installation. */
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const {chromium} = require(process.env.PLAYWRIGHT_PATH || 'playwright-core');
(async()=>{
 const browser=await chromium.launch({executablePath:process.env.CHROME_PATH||'/usr/bin/google-chrome',headless:true,args:['--no-sandbox']});
 try{
 const page=await browser.newPage({viewport:{width:1440,height:1100}}),errors=[];
 page.on('pageerror',e=>errors.push(e.message));
 page.on('requestfailed',request=>errors.push(`Request failed: ${request.url()} ${request.failure()?.errorText||''}`));
 await page.goto('http://127.0.0.1:8000/legacy');
 await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('GEMINI_API_KEY'));
 assert.equal(await page.locator('.empty').count(),1);
 await fs.mkdir('test-results',{recursive:true});
 await page.screenshot({path:'test-results/empty-desktop.png',fullPage:true});
 await page.getByRole('button',{name:'Open demonstration'}).click();
 await page.getByText('Demonstration — not a live verification. Synthetic context; curated assessment.',{exact:true}).waitFor();
 assert.equal(await page.getByText('Researcher decision: pending',{exact:true}).count(),1);
 await page.getByLabel('Your final wording').fill('Synthetic result: puncta count alone does not resolve flux.');
 await page.getByLabel('Researcher notes').fill('Checked the abstract-only limitation.');
 await page.getByRole('button',{name:'Save edited wording',exact:true}).click();
 await page.getByText('Researcher decision: edited',{exact:true}).waitFor();
 const downloadPromise=page.waitForEvent('download');
 await page.getByRole('button',{name:'Download JSON',exact:true}).click();
 const download=await downloadPromise;
 const exported=JSON.parse(await fs.readFile(await download.path(),'utf8'));
 assert.equal(exported.mode,'demo');assert.equal(exported.claims[0].decision.status,'edited');
 assert.equal(exported.claims[0].decision.notes,'Checked the abstract-only limitation.');
 assert.equal(exported.sources.length,2);assert.equal(exported.model_runs.length,0);
 await page.screenshot({path:'test-results/demo-desktop.png',fullPage:true});
 await page.getByRole('button',{name:'Reject',exact:true}).click();
 await page.getByText('Researcher decision: rejected',{exact:true}).waitFor();
 await page.getByLabel('Answer or claim to review').fill('<img src=x onerror="window.INJECTED=true"> is untrusted text.');
 await page.getByRole('button',{name:'Start live review'}).click();
 await page.waitForFunction(()=>document.querySelector('#status').textContent.includes('sign in with Google first'));
 assert.equal(await page.evaluate(()=>window.INJECTED),undefined);
 assert.equal(await page.locator('.claim img').count(),0);
 assert.equal(await page.getByText('Researcher decision: rejected',{exact:true}).count(),1);
 await page.setViewportSize({width:390,height:844});
 await page.screenshot({path:'test-results/live-mobile.png',fullPage:true});
 assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth>window.innerWidth),false);
 assert.deepEqual(errors,[]);
 console.log('Legacy browser smoke passed: empty/demo, edited/rejected decisions, JSON provenance, signed-out live rejection, safe text rendering, mobile overflow; no page errors.');
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
