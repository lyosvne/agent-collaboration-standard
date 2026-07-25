const fs = require('fs');
const path = require('path');
const { spawnSync } = require('child_process');

const base = path.join(__dirname, '..');
const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8'));
const larkCli = config.feishu.lark_cli_path;
const chatId = config.feishu.self_chat_id;
const checkpointFile = path.join(base, 'raw', 'daily-checkpoint.json');
const today = new Date().toISOString().slice(0, 10);
const outFile = path.join(base, 'raw', `daily-messages-${today}.json`);

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
    throw new Error('Parse error: ' + out.slice(0, 200));
  }
}

if (!larkCli) { console.log('No lark_cli_path configured'); process.exit(0); }

let checkpoint = { last_position: '2850' };
if (fs.existsSync(checkpointFile)) {
  checkpoint = JSON.parse(fs.readFileSync(checkpointFile, 'utf8'));
}

// For first run, set checkpoint to current last known position from original audit (position ~2836)
// so we only get NEW messages after the audit
console.log('Checkpoint position:', checkpoint.last_position);

let allMessages = [];
let hasMore = true;
let pageToken = '';
let safetyCount = 0;

while (hasMore && safetyCount < 20) {
  safetyCount++;
  const args = ['im', '+chat-messages-list', '--chat-id', chatId, '--as', 'user', '--page-size', '50', '--format', 'json', '--sort', 'desc'];
  if (pageToken) args.push('--page-token', pageToken);
  
  const data = runLarkCli(args);
  if (!data.ok) { console.log('API error:', JSON.stringify(data.error)); break; }
  
  const messages = data.data?.messages || [];
  allMessages = allMessages.concat(messages);
  hasMore = data.data?.has_more;
  pageToken = data.data?.page_token;
  
  const lastMsg = messages[messages.length - 1];
  if (lastMsg && parseInt(lastMsg.message_position) <= parseInt(checkpoint.last_position)) break;
  
  console.log('  Page', safetyCount, 'got', messages.length, 'messages');
}

const newMessages = allMessages.filter(m => parseInt(m.message_position) > parseInt(checkpoint.last_position));
console.log('Total fetched:', allMessages.length, 'New:', newMessages.length);

if (newMessages.length > 0) {
  const maxPos = Math.max(...newMessages.map(m => parseInt(m.message_position)));
  checkpoint.last_position = String(maxPos);
  checkpoint.updated_at = new Date().toISOString();
  fs.writeFileSync(checkpointFile, JSON.stringify(checkpoint, null, 2), 'utf8');
  
  let existing = [];
  if (fs.existsSync(outFile)) { try { existing = JSON.parse(fs.readFileSync(outFile, 'utf8')); } catch(e) {} }
  const combined = [...newMessages.reverse(), ...existing];
  fs.writeFileSync(outFile, JSON.stringify(combined, null, 2), 'utf8');
  
  const wechatUrls = [], githubUrls = [];
  for (const msg of newMessages) {
    const content = msg.content || '';
    (content.match(/https?:\/\/mp\.weixin\.qq\.com\/[^\s"<>]+/g) || []).forEach(u => wechatUrls.push({ url: u.replace(/&amp;/g, '&'), time: msg.create_time, msg_id: msg.message_id }));
    (content.match(/https?:\/\/github\.com\/[^\s"<>]+/g) || []).forEach(u => githubUrls.push({ url: u.replace(/&amp;/g, '&'), time: msg.create_time, msg_id: msg.message_id }));
  }
  
  const wcFile = path.join(base, 'raw', `daily-wechat-urls-${today}.json`);
  const ghFile = path.join(base, 'raw', `daily-github-urls-${today}.json`);
  let exWc = [], exGh = [];
  if (fs.existsSync(wcFile)) { try { exWc = JSON.parse(fs.readFileSync(wcFile, 'utf8')); } catch(e) {} }
  if (fs.existsSync(ghFile)) { try { exGh = JSON.parse(fs.readFileSync(ghFile, 'utf8')); } catch(e) {} }
  fs.writeFileSync(wcFile, JSON.stringify([...wechatUrls, ...exWc], null, 2), 'utf8');
  fs.writeFileSync(ghFile, JSON.stringify([...githubUrls, ...exGh], null, 2), 'utf8');
  
  console.log('WeChat URLs:', wechatUrls.length);
  console.log('GitHub URLs:', githubUrls.length);
} else {
  console.log('No new messages');
}
