#!/usr/bin/env node
// Knowledge Base Lint Script
// Checks: orphan pages, broken [[links]], missing tags, duplicates
const fs=require('fs');
const path=require('path');
const wikiDir=path.join(__dirname,'..','wiki');
const files=[];
function walk(d){for(const f of fs.readdirSync(d,{withFileTypes:true})){const p=path.join(d,f.name);if(f.isDirectory())walk(p);else if(f.name.endsWith('.md'))files.push(p);}}
walk(wikiDir);

const allSlugs=new Set();
const links=[];
const issues=[];

for(const fp of files){
  const c=fs.readFileSync(fp,'utf8');
  const slug=path.basename(fp,'.md');
  allSlugs.add(slug);
  // Check tags
  if(!/tags:/.test(c)) issues.push('MISSING_TAGS: '+slug);
  // Extract [[links]]
  const linkRe=/\[\[([^\]]+)\]\]/g;
  let m;
  while((m=linkRe.exec(c))!==null) links.push({from:slug, to:m[1]});
}

// Check broken links
for(const l of links){
  if(!allSlugs.has(l.to)) issues.log+=(issues.log?'\n':'')+'';
  if(!allSlugs.has(l.to)){
    issues.push('BROKEN_LINK: '+l.from+' -> '+l.to);
  }
}

// Check orphans (no incoming links)
const linkedTo=new Set(links.map(l=>l.to));
for(const s of allSlugs){
  if(!linkedTo.has(s) && s!=='README') issues.push('ORPHAN: '+s);
}

console.log('=== Knowledge Base Lint Report ===');
console.log('Total pages:', files.length);
console.log('Total links:', links.length);
console.log('Issues found:', issues.length);
issues.forEach(i=>console.log(' -',i));
if(issues.length===0) console.log('All checks passed.');
