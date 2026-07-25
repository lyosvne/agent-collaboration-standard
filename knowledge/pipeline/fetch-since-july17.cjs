const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const base = path.join(__dirname, '..');
const larkCli = 'C:\\Users\\Admin\\AppData\\Roaming\\npm\\lark-cli.ps1';
const chatId = 'oc_52c68d36f05c845d45d9312fd25158a4';

function runLarkCli(args) {
  const psArgs = ['-NoProfile', '-File', larkCli, ...args];
  const r = spawnSync('C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe', psArgs, {
    encoding: 'utf8', timeout: 60000, maxBuffer: 10 * 1024 * 1024
  });
  let out = (r.stdout || '').replace(/^node\.exe :.*\n/gm, '').replace(/^At .*\n/gm, '')
    .replace(/^\+ .*\n/gm, '').replace(/^所在位置.*\n/gm, '')
    .replace(/^CategoryInfo.*\n/gm, '').replace(/^FullyQualifiedErrorId.*\n/gm, '').trim();
  try { return JSON.parse(out); }
  catch(e) {
    const m = out.match(/\{[\s\S]*\}/);
    if (m) try { return JSON.parse(m[0]); } catch(e2) {}
    console.log('Raw output:', out.slice(0, 500));
    throw new Error('Parse error');
  }
}

// July 17 2026 00:00:00+08:00 in ISO 8601
const startTime = '2026-07-17T00:00:00+08:00';
console.log('Fetching messages since', startTime);

let allMessages = [];
let hasMore = true;
let pageToken = '';
let pages = 0;

while (hasMore && pages < 30) {
  pages++;
  const args = ['im', '+chat-messages-list', '--chat-id', chatId, '--as', 'user',
    '--page-size', '50', '--format', 'json', '--start', startTime, '--sort', 'desc'];
  if (pageToken) args.push('--page-token', pageToken);
  
  const data = runLarkCli(args);
  if (!data.ok) { console.log('Error:', JSON.stringify(data.error)); break; }
  
  const messages = data.data?.messages || [];
  allMessages = allMessages.concat(messages);
  hasMore = data.data?.has_more;
  pageToken = data.data?.page_token;
  console.log('  Page', pages, 'got', messages.length, 'total:', allMessages.length);
}

console.log('Total messages since July 17:', allMessages.length);

const wechatMsgs = [];
const githubMsgs = [];
for (const msg of allMessages) {
  const content = msg.content || '';
  const wcUrls = content.match(/https?:\/\/mp\.weixin\.qq\.com\/[^\s"<>]+/g);
  const ghUrls = content.match(/https?:\/\/github\.com\/[^\s"<>]+/g);
  if (wcUrls) wcUrls.forEach(u => wechatMsgs.push({ time: msg.create_time, url: u.replace(/&amp;/g,'&'), msg_id: msg.message_id, position: msg.message_position }));
  if (ghUrls) ghUrls.forEach(u => githubMsgs.push({ time: msg.create_time, url: u.replace(/&amp;/g,'&'), msg_id: msg.message_id }));
}

console.log('WeChat URLs:', wechatMsgs.length);
console.log('GitHub URLs:', githubMsgs.length);

// Compare with existing
const existingArticles = JSON.parse(fs.readFileSync(path.join(base, 'analysis/articles-content-deep.json'), 'utf8'));
const existingUrls = new Set(existingArticles.results.map(r => r.url));
const existingFulltext = JSON.parse(fs.readFileSync(path.join(base, 'raw/articles-fulltext.json'), 'utf8'));
// Handle BOM
let eftRaw = JSON.stringify(existingFulltext);
const eftUrls = new Set();
if (existingFulltext && typeof existingFulltext === 'object') {
  Object.keys(existingFulltext).forEach(k => eftUrls.add(k));
}
// Also check daily
const today = new Date().toISOString().slice(0,10);
const dailyFile = path.join(base, 'raw', 'daily-articles-fulltext-' + today + '.json');
if (fs.existsSync(dailyFile)) {
  const daily = JSON.parse(fs.readFileSync(dailyFile, 'utf8'));
  Object.keys(daily).forEach(k => eftUrls.add(k));
}

const missingFromFulltext = wechatMsgs.filter(m => !eftUrls.has(m.url) && !existingUrls.has(m.url));
console.log('\nAlready analyzed:', wechatMsgs.filter(m => eftUrls.has(m.url) || existingUrls.has(m.url)).length);
console.log('NEW (not yet in knowledge base):', missingFromFulltext.length);
if (missingFromFulltext.length > 0) {
  missingFromFulltext.forEach(a => console.log(' ', a.time, a.url));
}

fs.writeFileSync(path.join(base, 'raw', 'messages-since-july17.json'), JSON.stringify(allMessages, null, 2), 'utf8');
fs.writeFileSync(path.join(base, 'raw', 'new-wechat-urls-july17.json'), JSON.stringify(missingFromFulltext, null, 2), 'utf8');
