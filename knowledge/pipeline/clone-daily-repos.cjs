const fs = require('fs');
const path = require('path');
const { execSync } = require('child_process');

const config = JSON.parse(fs.readFileSync(path.join(__dirname, 'config.json'), 'utf8'));
const base = config.paths.base;
const reposDir = path.join(base, 'repos');
const today = new Date().toISOString().slice(0, 10);
const ghFile = path.join(base, 'raw', `daily-github-urls-${today}.json`);

if (!fs.existsSync(ghFile)) {
  console.log('No GitHub URLs for today, skipping');
  process.exit(0);
}

const urls = JSON.parse(fs.readFileSync(ghFile, 'utf8'));
const uniqueRepos = JSON.parse(fs.readFileSync(path.join(base, 'analysis/unique-repos-list.json'), 'utf8'));
const finalData = JSON.parse(fs.readFileSync(path.join(base, 'analysis/per-repo-final.json'), 'utf8'));
const meta = JSON.parse(fs.readFileSync(path.join(base, 'analysis/repo-metadata.json'), 'utf8'));

const knownSet = new Set(uniqueRepos.map(r => (r.owner + '/' + r.repo).toLowerCase()));
finalData.forEach(r => knownSet.add((r.fullName || '').toLowerCase()));

const newRepos = [];
const seen = new Set();
for (const u of urls) {
  const match = u.url.match(/github\.com\/([^\/]+)\/([^\/\?#\)]+)/);
  if (!match) continue;
  const owner = match[1], repo = match[2].replace(/\.git$/, '');
  const full = (owner + '/' + repo).toLowerCase();
  if (seen.has(full) || knownSet.has(full)) continue;
  seen.add(full);
  newRepos.push({ owner, repo, fullName: owner + '/' + repo, source_url: u.url, time: u.time });
}

console.log('New repos to process:', newRepos.length);
if (newRepos.length === 0) process.exit(0);
if (!fs.existsSync(reposDir)) fs.mkdirSync(reposDir, { recursive: true });

let cloned = 0, failed = 0;
for (const repo of newRepos) {
  const dirName = repo.owner + '__' + repo.repo;
  const dirPath = path.join(reposDir, dirName);
  if (fs.existsSync(dirPath)) { cloned++; continue; }
  try {
    console.log('  Cloning', repo.fullName + '...');
    execSync(`git clone --depth 1 "https://github.com/${repo.owner}/${repo.repo}.git" "${dirPath}"`, { stdio: 'pipe', timeout: 120000 });
    cloned++;
    uniqueRepos.push({ owner: repo.owner, repo: repo.repo });
    // Fetch star via gh CLI (authenticated, 5000/hr)
    try {
      const ghRes = execSync(`gh api repos/${repo.owner}/${repo.repo}`, { encoding: 'utf8', timeout: 15000 });
      const d = JSON.parse(ghRes);
      if (d.stargazers_count !== undefined) {
        meta[repo.fullName] = {
          full_name: d.full_name, stars: d.stargazers_count, forks: d.forks_count,
          language: d.language, pushed_at: d.pushed_at, description: d.description,
          topics: d.topics || [], archived: d.archived, fetchedAt: Date.now()
        };
        console.log('    ⭐', d.stargazers_count);
      }
    } catch(e) { console.log('    Star fetch skipped'); }
  } catch(e) {
    console.log('  FAILED:', repo.fullName);
    failed++;
  }
}

fs.writeFileSync(path.join(base, 'analysis/unique-repos-list.json'), JSON.stringify(uniqueRepos, null, 2), 'utf8');
fs.writeFileSync(path.join(base, 'analysis/repo-metadata.json'), JSON.stringify(meta, null, 2), 'utf8');
fs.writeFileSync(path.join(base, 'raw', `daily-new-repos-${today}.json`), JSON.stringify(newRepos, null, 2), 'utf8');
console.log(`Done: ${cloned} ok, ${failed} failed`);
