const fs = require('node:fs');
const path = require('node:path');
const root = path.resolve(__dirname, '..');
const out = path.join(root, 'vercel-public');
fs.rmSync(out, { recursive: true, force: true });
fs.mkdirSync(out, { recursive: true });
fs.copyFileSync(path.join(root, 'studio-app/static/index.html'), path.join(out, 'index.html'));
fs.cpSync(path.join(root, 'studio-app/static'), path.join(out, 'static'), { recursive: true });
console.log('Built Vercel frontend from studio-app/static');
