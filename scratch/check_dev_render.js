import { chromium } from 'playwright';
import { createServer } from 'vite';

(async () => {
  const server = await createServer({
    server: { port: 5173 }
  });
  await server.listen();
  console.log('Vite dev server running on http://localhost:5173');

  const browser = await chromium.launch();
  const page = await browser.newPage();
  
  page.on('console', msg => console.log('DEV_BROWSER_CONSOLE:', msg.type(), msg.text()));
  page.on('pageerror', error => console.error('DEV_BROWSER_ERROR:', error));
  
  try {
    await page.goto('http://localhost:5173', { waitUntil: 'networkidle' });
    const content = await page.content();
    console.log('PAGE_TITLE:', await page.title());
    console.log('HTML_LENGTH:', content.length);
    const rootHTML = await page.$eval('#root', el => el.innerHTML);
    console.log('ROOT_INNER_HTML_LENGTH:', rootHTML.length);
    if (rootHTML.length === 0) {
      console.error('ROOT IS EMPTY! RENDER FAILED!');
    } else {
      console.log('ROOT HAS CONTENT - RENDER SUCCESSFUL!');
    }
  } catch (err) {
    console.error('FAILED TO LOAD OR RENDER PAGE:', err);
  } finally {
    await browser.close();
    await server.close();
  }
})();
