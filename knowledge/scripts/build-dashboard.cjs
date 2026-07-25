const fs = require('fs');
const path = require('path');
const kb = path.join(__dirname, '..');
const wiki = path.join(kb, 'wiki');
const auditDir = path.join(kb, '..');

const pages = [];
function walk(d, cat) {
  for (const f of fs.readdirSync(d, {withFileTypes:true})) {
    const p = path.join(d, f.name);
    if (f.isDirectory()) walk(p, f.name);
    else if (f.name.endsWith('.md')) {
      const c = fs.readFileSync(p, 'utf8');
      const title = (c.match(/^#\s+(.+)$/m)||[,''])[1];
      const tags = (c.match(/tags:\s*\[(.+?)\]/)||[,''])[1].split(',').map(s=>s.trim()).filter(Boolean);
      pages.push({file: f.name, path: p.replace(kb+path.sep,''), category: cat, title, tags});
    }
  }
}
walk(wiki, 'wiki');

const v2 = JSON.parse(fs.readFileSync(path.join(auditDir, 'analysis/full-code-index-v2.json'), 'utf8'));
const totalFiles = v2.reduce((s,r)=>s+r.codeFiles,0);
const totalSkills = v2.reduce((s,r)=>s+r.skillCount,0);

const catNames = {agents:'Agents',projects:'Projects',rules:'Rules',insights:'Insights',skills:'Skills','oss-projects':'OSS Projects'};
const grouped = {};
pages.forEach(p => { if(!grouped[p.category]) grouped[p.category]=[]; grouped[p.category].push(p); });

let catsHtml = '';
for (const [k,v] of Object.entries(grouped)) {
  catsHtml += '<div class="cat"><h2>'+(catNames[k]||k)+' ('+v.length+')</h2>';
  catsHtml += v.map(p => '<div class="item"><div class="t">'+p.title+'</div><div class="tags">'+p.tags.map(t=>'<span class="tag">'+t+'</span>').join('')+'</div></div>').join('');
  catsHtml += '</div>';
}

const html = '<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Knowledge Dashboard</title><style>*{box-sizing:border-box;margin:0;padding:0}body{font-family:-apple-system,BlinkMacSystemFont,Segoe UI,sans-serif;background:#0f172a;color:#e2e8f0;padding:20px}h1{font-size:1.5rem;margin-bottom:8px}.sub{color:#94a3b8;margin-bottom:20px}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(130px,1fr));gap:12px;margin-bottom:24px}.stat{background:#1e293b;border-radius:8px;padding:16px;text-align:center}.stat .n{font-size:1.6rem;font-weight:700;color:#38bdf8}.stat .l{font-size:.7rem;color:#94a3b8;margin-top:4px}.search{width:100%;padding:12px;background:#1e293b;border:1px solid #334155;border-radius:8px;color:#e2e8f0;font-size:1rem;margin-bottom:20px}.cats{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px}.cat{background:#1e293b;border-radius:8px;padding:16px}.cat h2{font-size:.9rem;color:#38bdf8;margin-bottom:12px}.item{padding:8px 0;border-bottom:1px solid #334155}.item:last-child{border:none}.item .t{font-size:.85rem}.item:hover .t{color:#38bdf8}.item .tags{margin-top:4px;display:flex;gap:4px;flex-wrap:wrap}.tag{font-size:.6rem;background:#334155;color:#94a3b8;padding:2px 6px;border-radius:4px}</style></head><body><h1>Knowledge Dashboard</h1><p class="sub">Karpathy LLM Wiki | knowledge-audit-2026-07 | '+pages.length+' pages</p><div class="stats"><div class="stat"><div class="n">323</div><div class="l">OSS Repos</div></div><div class="stat"><div class="n">'+Math.round(totalFiles/1000)+'K</div><div class="l">Source Files</div></div><div class="stat"><div class="n">'+totalSkills+'</div><div class="l">Skills</div></div><div class="stat"><div class="n">489</div><div class="l">WeChat Articles</div></div><div class="stat"><div class="n">'+pages.length+'</div><div class="l">Wiki Pages</div></div></div><input class="search" type="text" placeholder="Search knowledge..." oninput="filter(this.value)"><div class="cats">'+catsHtml+'</div><script>function filter(q){q=q.toLowerCase();document.querySelectorAll(".item").forEach(function(e){e.style.display=e.textContent.toLowerCase().includes(q)?"":"none"})}</script></body></html>';

fs.writeFileSync(path.join(kb, 'dashboard.html'), html, 'utf8');
console.log('Dashboard:', html.length, 'bytes,', pages.length, 'pages');
