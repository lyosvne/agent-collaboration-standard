const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');
const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8').replace(/^\uFEFF/, ''));
const base = config.paths.base;
function today() { return new Date().toISOString().slice(0, 10); }
function log(m) {
  const ts = new Date().toISOString().substring(11, 19);
  const l = '[' + ts + '] ' + m;
  console.log(l);
  fs.appendFileSync(path.join(base, 'daily', 'log-' + today() + '.txt'), l + '\n', 'utf8');
}
function run(cmd, opts) {
  try { return execSync(cmd, { encoding: 'utf8', timeout: 600000, maxBuffer: 50*1024*1024, ...opts }); }
  catch (e) { log('WARN: ' + e.message.slice(0, 200)); return null; }
}

// Persist last run timestamp
const lastRunFile = path.join(base, 'daily', 'last-run.json');
let lastRun = null;
if (fs.existsSync(lastRunFile)) {
  try { lastRun = JSON.parse(fs.readFileSync(lastRunFile, 'utf8')); } catch {}
}
const now = new Date();
const lookbackDays = lastRun ? Math.min(14, Math.max(1, Math.ceil((now - new Date(lastRun.timestamp)) / 86400000) + 1)) : 7;
log('=== Daily Knowledge Pipeline ===');
log('Date: ' + today());
log('Last run: ' + (lastRun ? lastRun.timestamp : 'never') + ', lookback: ' + lookbackDays + ' days');

// STEP 1: Fetch Feishu messages
log('>>> STEP 1: Fetch Feishu messages');
const lookbackDate = new Date(Date.now() - lookbackDays*86400000).toISOString();
const msgFile = path.join(base, 'raw', 'daily-messages-' + today() + '.json');
const larkCli = config.feishu.lark_cli_path;
let msgs = [];
if (larkCli && fs.existsSync(larkCli)) {
  try {
    const psCmd = '& "' + larkCli + '" im +chat-messages-list --chat-id ' + config.feishu.self_chat_id + ' --start "' + lookbackDate + '" --order desc --page-size 50 --json';
    const r = execSync('powershell -NoProfile -Command "' + psCmd + '"', { encoding: 'utf8', timeout: 30000 });
    const jm = r.match(/\{[\s\S]*\}\s*$/);
    if (jm) { const p = JSON.parse(jm[0]); if (p.ok && p.data && p.data.messages) msgs = p.data.messages; }
  } catch (e) { log('lark-cli error: ' + e.message.slice(0, 150)); }
}
if (msgs.length > 0) { fs.writeFileSync(msgFile, JSON.stringify(msgs, null, 2), 'utf8'); log('Saved ' + msgs.length + ' messages'); }
else { log('No new messages'); }

// STEP 2: Extract URLs
log('>>> STEP 2: Extract URLs');
let wechatUrls = [], githubUrls = [];
if (msgs.length > 0) {
  msgs.forEach(function(m) {
    const c = m.content || '';
    (c.match(/https?:\/\/mp\.weixin\.qq\.com\/s\/[^\s"<>\)]+/g) || []).forEach(u => wechatUrls.push(u.replace(/&amp;/g, '&')));
    (c.match(/https?:\/\/github\.com\/[^\s"<>\)]+\/[^\s"<>\)]+/g) || []).forEach(u => githubUrls.push(u.replace(/&amp;/g, '&').replace(/\.git$/, '')));
  });
}
wechatUrls = [...new Set(wechatUrls)];
githubUrls = [...new Set(githubUrls)];
fs.writeFileSync(path.join(base, 'raw', 'daily-wechat-urls-' + today() + '.json'), JSON.stringify(wechatUrls, null, 2), 'utf8');
fs.writeFileSync(path.join(base, 'raw', 'daily-github-urls-' + today() + '.json'), JSON.stringify(githubUrls, null, 2), 'utf8');
log('Found ' + wechatUrls.length + ' WeChat URLs, ' + githubUrls.length + ' GitHub URLs');

// STEP 3: Fetch WeChat article fulltext
log('>>> STEP 3: Fetch WeChat article fulltext');
if (wechatUrls.length > 0) {
  const r = run('node scripts/daily-fetch-fulltext.cjs', { cwd: base, timeout: 600000 });
  if (r) console.log(r.trim());
} else { log('No WeChat URLs'); }

// STEP 4: Clone new GitHub repos
log('>>> STEP 4: Clone and scan new GitHub repos');
if (githubUrls.length > 0) {
  const r = run('node scripts/clone-daily-repos.cjs', { cwd: base, timeout: 600000 });
  if (r) console.log(r.trim());
} else { log('No new GitHub URLs'); }

// STEP 5: Regenerate wiki
log('>>> STEP 5: Regenerate wiki');
run('node scripts/gen-wiki-clean.cjs', { cwd: base });
log('Wiki regenerated');

// STEP 6: Daily summary
log('>>> STEP 6: Daily summary');
const insightsDir = path.join(base, 'Knowledge', 'wiki', 'insights');
if (!fs.existsSync(insightsDir)) fs.mkdirSync(insightsDir, { recursive: true });
const summary = '---\ntitle: Daily Digest ' + today() + '\ntags: [daily,digest]\ncreated: ' + today() + '\nlookback: ' + lookbackDays + 'd\n---\n# Daily Digest - ' + today() + '\n\n## Stats\n- New messages: ' + msgs.length + '\n- New WeChat articles: ' + wechatUrls.length + '\n- New GitHub repos: ' + githubUrls.length + '\n- Lookback: ' + lookbackDays + ' days\n\n## New Articles\n' + wechatUrls.map(u => '- ' + u).join('\n') + '\n\n## New Projects\n' + githubUrls.map(u => '- ' + u).join('\n') + '\n\n---\n*Generated at ' + new Date().toISOString() + '*\n';
fs.writeFileSync(path.join(insightsDir, 'daily-' + today() + '.md'), summary, 'utf8');
log('Summary written');

// Save last run timestamp
fs.writeFileSync(lastRunFile, JSON.stringify({ timestamp: now.toISOString(), messages: msgs.length, wechatUrls: wechatUrls.length, githubUrls: githubUrls.length }, null, 2), 'utf8');
log('Last-run checkpoint saved');
log('=== Pipeline Complete ===');