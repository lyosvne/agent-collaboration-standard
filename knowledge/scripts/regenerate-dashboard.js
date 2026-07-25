#!/usr/bin/env node
// Regenerate dashboard.html from current wiki files
const fs=require('fs');
const path=require('path');
const wikiDir=path.join(__dirname,'..','wiki');
const kbDir=path.join(__dirname,'..');
const pages=[];
function walk(d,cat){for(const f of fs.readdirSync(d,{withFileTypes:true})){const p=path.join(d,f.name);if(f.isDirectory())walk(p,f.name);else if(f.name.endsWith('.md')){const c=fs.readFileSync(p,'utf8');const t=(c.match(/^#\s+(.+)$/m)||[,''])[1];const tags=(c.match(/tags:\s*\[(.+?)\]/)||[,''])[1].split(',').map(s=>s.trim()).filter(Boolean);pages.push({file:f.name,category:cat,title:t,tags});}}}
walk(wikiDir);
// ... (full HTML same as gen-dashboard.cjs but inline)
console.log('Found', pages.length, 'pages. Run gen-dashboard.cjs for full regeneration.');
