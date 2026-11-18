// Run with: node scripts/browser_review.cjs <absolute path to playwright package>
const { chromium } = require(process.argv[2]);
const fs = require('node:fs');
(async () => {
  const browser = await chromium.launch({channel:'msedge', headless:true});
  const page = await browser.newPage({viewport:{width:1440,height:1000}});
  const errors = [];
  page.on('pageerror', e => errors.push(e.message));
  fs.mkdirSync('.impeccable/review', {recursive:true});
  await page.goto('http://localhost:5173');
  await page.getByText('Server ready', {exact:true}).waitFor();
  await page.mouse.move(0,0); await page.waitForTimeout(300); await page.screenshot({path:'.impeccable/review/welcome.png',fullPage:true});
  await page.getByRole('button',{name:'Design network',exact:true}).click();
  await page.getByText('The simulated plan passes its checks.',{exact:true}).waitFor();
  await page.mouse.move(0,0); await page.waitForTimeout(300); await page.screenshot({path:'.impeccable/review/desktop.png',fullPage:true});
  await page.getByRole('navigation',{name:'Design results'}).getByRole('button',{name:'Network map',exact:true}).click();
  await page.locator('.toolbar select').nth(0).selectOption('Guest-C');
  await page.locator('.toolbar select').nth(1).selectOption('Servers');
  await page.getByRole('button',{name:'Trace packet',exact:true}).click();
  await page.getByRole('heading',{name:'Connection blocked'}).waitFor();
  await page.mouse.move(0,0); await page.waitForTimeout(300); await page.screenshot({path:'.impeccable/review/network.png',fullPage:true});
  for (const tab of ['Why these choices?','Address plan','Device instructions','Checks','Security','Equipment & costs','Saved versions','Export & report']) {
    await page.getByRole('navigation',{name:'Design results'}).getByRole('button',{name:tab,exact:true}).click();
  }
  await page.emulateMedia({media:'print'});
  await page.pdf({path:'.impeccable/review/campus-report.pdf',format:'A4',printBackground:true});
  await page.emulateMedia({media:'screen'});
  await page.getByRole('navigation',{name:'Design results'}).getByRole('button',{name:'How to use',exact:true}).click();
  await page.mouse.move(0,0); await page.waitForTimeout(300); await page.screenshot({path:'.impeccable/review/guide.png',fullPage:true});
  await page.setViewportSize({width:390,height:844});
  await page.getByRole('navigation',{name:'Design results'}).getByRole('button',{name:'Overview',exact:true}).click();
  await page.mouse.move(0,0); await page.waitForTimeout(300); await page.screenshot({path:'.impeccable/review/mobile.png',fullPage:true});
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth > innerWidth);
  await page.getByRole('navigation',{name:'Design results'}).getByRole('button',{name:'Network map',exact:true}).click();
  await page.mouse.move(0,0); await page.waitForTimeout(300);
  await page.screenshot({path:'.impeccable/review/mobile-map.png',fullPage:true});
  await page.setViewportSize({width:1440,height:1000});
  await page.getByLabel('Theme',{exact:true}).selectOption('dark');
  await page.mouse.move(0,0); await page.waitForTimeout(300);
  await page.screenshot({path:'.impeccable/review/dark.png',fullPage:true});
  await page.getByLabel('Theme',{exact:true}).selectOption('light');
  const nav = page.getByRole('navigation',{name:'Design results'});
  for (const preset of ['metro_man','global_wan']) {
    await page.getByLabel('Choose a starting point').selectOption(preset);
    await page.waitForFunction(name => JSON.parse(document.querySelector('#json').value).profile === name, preset);
    await page.getByRole('button',{name:'Design network',exact:true}).click();
    await page.getByRole('button',{name:'Design network',exact:true}).waitFor();
    await page.getByText('The simulated plan passes its checks.',{exact:true}).waitFor();
    if (preset === 'metro_man') {
      await nav.getByRole('button',{name:'Network map',exact:true}).click();
      await page.locator('.toolbar select').nth(0).selectOption('Branch-Users');
      await page.locator('.toolbar select').nth(1).selectOption('Colo-Trading');
      await page.locator('.toolbar select').nth(2).selectOption('tcp');
      await page.getByLabel('Port',{exact:true}).fill('443');
      await page.getByRole('button',{name:'Trace packet',exact:true}).click();
      await page.getByRole('heading',{name:'Connection delivered',exact:true}).waitFor();
      await page.locator('.toolbar select').nth(2).selectOption('icmp');
      await page.getByRole('button',{name:'Trace packet',exact:true}).click();
      await page.getByRole('heading',{name:'Connection blocked',exact:true}).waitFor();
      await page.getByLabel('Enable failure testing').check();
      await page.getByRole('button',{name:'Fail link HQ-R1 to BRANCH-R1',exact:true}).press('Enter');
      await page.getByRole('heading',{name:/Network survives:/}).waitFor();
      await page.getByRole('button',{name:'Clear',exact:true}).click();
    }
    await nav.getByRole('button',{name:'Export & report',exact:true}).click();
    for (const button of ['Download configs + reports (.zip)','Report (.md)','Design (.json)','Cabling guide']) {
      const downloadEvent = page.waitForEvent('download');
      await page.getByRole('button',{name:button,exact:true}).click();
      const file = await downloadEvent;
      if (await file.failure()) throw new Error('Download failed: '+button);
      await file.saveAs('.impeccable/review/'+file.suggestedFilename());
    }
  }
  await page.route('**/export/zip', route => route.fulfill({status:503,body:'Unavailable'}));
  await page.getByRole('button',{name:'Download configs + reports (.zip)',exact:true}).click();
  await page.getByRole('alert').filter({hasText:'download could not finish'}).waitFor();
  await browser.close();
  if (errors.length || overflow) throw new Error(JSON.stringify({errors,overflow}));
  console.log('Browser review passed: all three real API designs, allowed/denied traces, TCP-to-ICMP switch, keyboard failure simulation, downloads, export error recovery, all views, guide, print, mobile without page overflow.');
})().catch(e=>{console.error(e);process.exit(1)});

