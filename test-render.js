import { chromium } from 'playwright';
import { preview } from 'vite';

(async () => {
  const server = await preview({ preview: { port: 3000 } });
  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('BROWSER_CONSOLE:', msg.text()));
  page.on('pageerror', error => console.error('BROWSER_ERROR:', error));
  
  await page.goto('http://localhost:3000');
  await page.waitForTimeout(2000);
  
  await browser.close();
  server.httpServer.close();
})();
