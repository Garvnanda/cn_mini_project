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
  await browser.close();
  if (errors.length || overflow) throw new Error(JSON.stringify({errors,overflow}));
  console.log('Browser review passed: real API design, denied trace, all result views, guide, print, mobile without page overflow.');
})().catch(e=>{console.error(e);process.exit(1)});

