#!/usr/bin/env node
// Ingest a new article URL into knowledge base
// Usage: node ingest.js <url>
const fs=require('fs');
const path=require('path');
console.log('To ingest: send the article URL to Codex with instruction "save to Knowledge base"');
console.log('Codex will: 1) fetch full text 2) extract key points 3) create/update wiki pages 4) link to existing pages');
