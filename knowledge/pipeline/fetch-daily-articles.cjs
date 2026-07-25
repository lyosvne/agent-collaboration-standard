const { chromium } = require('C:/Users/Admin/AppData/Local/trae-tools/wechat-playwright-reader/node_modules/playwright');
const fs = require('fs');

const urlFile = process.argv[2];
const outFile = process.argv[3];

if (!urlFile || !outFile) {
  console.error('Usage: node fetch-daily-articles.cjs <urls.json> <output.json>');
  process.exit(1);
}

let raw = fs.readFileSync(urlFile, 'utf8');
if (raw.charCodeAt(0) === 0xFEFF) raw = raw.slice(1);
const urls = JSON.parse(raw);

let existing = {};
if (fs.existsSync(outFile)) {
  try { existing = JSON.parse(fs.readFileSync(outFile, 'utf8')); } catch(e) {}
}

const todo = urls.filter(u => !existing[u.url]);
console.log(`Total: ${urls.length}, done: ${Object.keys(existing).length}, todo: ${todo.length}`);

(async () => {
  const browser = await chromium.launch({ headless: true });
  for (let i = 0; i < todo.length; i++) {
    const u = todo[i];
    const context = await browser.newContext({
      userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/136.0.0.0 Safari/537.36',
      viewport: { width: 1440, height: 2200 },
      locale: 'zh-CN'
    });
    const page = await context.newPage();
    try {
      await page.goto(u.url, { waitUntil: 'domcontentloaded', timeout: 60000 });
      await page.waitForTimeout(3000);
      const data = await page.evaluate(() => {
        const cl = (v) => (typeof v === 'string' && v.trim().length > 0) ? v.trim() : null;
        const blocked = /环境异常|访问过于频繁|暂无权限|页面无法打开/i.test(document.body?.innerText || '');
        const title = cl(document.querySelector('#activity-name')?.textContent) || cl(document.querySelector('h1')?.textContent);
        const author = cl(document.querySelector('#js_name')?.textContent);
        const contentNode = document.querySelector('#js_content') || document.querySelector('.rich_media_content');
        const ct = cl(contentNode?.innerText) || '';
        const anchorUrls = [];
        contentNode?.querySelectorAll('a').forEach(a => { if (a.href) anchorUrls.push(a.href); });
        const textUrls = ct.match(/https?:\/\/[^\s\)\]\）]+/g) || [];
        const githubUrls = [...anchorUrls, ...textUrls].filter(x => x.includes('github.com'));
        return { title, author, blocked, textLength: ct.length, content: ct.slice(0, 50000), anchorUrls, textUrls, githubUrls };
      });
      existing[u.url] = { time: u.time, url: u.url, ok: !data.blocked, ...data };
      console.log(`[${i+1}/${todo.length}] ${data.title?.slice(0,50) || 'no title'} (${data.textLength} chars, ${data.githubUrls?.length||0} github urls)`);
    } catch(e) {
      existing[u.url] = { time: u.time, url: u.url, ok: false, error: e.message };
      console.log(`[${i+1}/${todo.length}] ERROR: ${e.message.slice(0,80)}`);
    }
    await context.close();
    if ((i+1) % 5 === 0 || i === todo.length - 1) {
      fs.writeFileSync(outFile, JSON.stringify(existing, null, 2), 'utf8');
    }
  }
  await browser.close();
  console.log('Done!');
})();
