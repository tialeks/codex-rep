#!/usr/bin/env node
import { createHash } from 'node:crypto';
import { lstat, mkdir, readFile, realpath, writeFile } from 'node:fs/promises';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const filenames = ['fonts.css', 'YS-Text-Regular.woff2', 'YS-Text-Medium.woff2', 'YS-Text-Bold.ttf', 'YS-Text-Cond-Black.ttf', 'YSCompressed-VF.woff2'];
const defaultManifest = 'https://s3.mds.yandex.net/plus-ultra-storybook/components/fonts/manifest.json';
const hash = bytes => createHash('sha256').update(bytes).digest('hex');
async function stat(path) {
  try { return await lstat(path); } catch (error) {
    if (error.code === 'ENOENT') return null;
    throw error;
  }
}
function httpsURL(value) {
  const url = new URL(value);
  if (url.protocol !== 'https:' || url.username || url.password || url.hash) throw new Error('Require HTTPS without credentials or fragments');
  return url;
}
async function download(url) {
  const response = await fetch(httpsURL(url), { redirect: 'error', signal: AbortSignal.timeout(60000) });
  if (!response.ok) throw new Error(`Download failed (HTTP ${response.status})`);
  return Buffer.from(await response.arrayBuffer());
}

export async function installFonts(args) {
  if (args.includes('--help')) {
    console.log(`Usage: node install-fonts.mjs [--manifest <fonts manifest path|HTTPS URL>] --project <existing package.json>\nDefaults to ${defaultManifest}; no manifest URL input is needed.\nUse --manifest only to override the default (for example, a local test release).\nVerifies six files before writes. Installs into public/fonts/adtechui. Refuses symlinks and conflicting files. Node.js 22+.`);
    return;
  }
  const options = {};
  for (let i = 0; i < args.length; i++) {
    const flag = args[i];
    if (!['--manifest', '--project'].includes(flag) || flag in options || !args[i + 1] || args[i + 1].startsWith('--')) throw new Error('Invalid arguments; see --help');
    options[flag] = args[++i];
  }
  if (!options['--project']) throw new Error('--project required');
  const project = resolve(options['--project']);
  if (!project.endsWith('/package.json') || !(await stat(project))?.isFile()) throw new Error('Project must be a regular package.json, not a symlink');
  const root = await realpath(dirname(project));
  const source = options['--manifest'] ?? defaultManifest;
  const remote = /^[A-Za-z][A-Za-z0-9+.-]*:/.test(source);
  const url = remote ? httpsURL(source) : null;
  const manifest = JSON.parse((remote ? await download(url) : await readFile(resolve(source))).toString('utf8'));
  if (manifest?.schemaVersion !== 1 || !Array.isArray(manifest.files) || manifest.files.length !== filenames.length) throw new Error('Invalid fonts manifest');
  const seen = new Set();
  for (const item of manifest.files) {
    if (!item || !filenames.includes(item.file) || seen.has(item.file)) throw new Error('Unsafe, unknown or duplicate font filename');
    if (typeof item.sha256 !== 'string' || item.sha256.length !== 64 || !/^[a-f0-9]{64}$/.test(item.sha256)) throw new Error('Invalid SHA-256');
    seen.add(item.file);
  }
  const folder = join(root, 'public/fonts/adtechui');
  for (const path of [join(root, 'public'), join(root, 'public/fonts'), folder]) {
    const existing = await stat(path);
    if (existing && !existing.isDirectory()) throw new Error('Static path must be a real directory, not a symlink');
  }
  const staged = [];
  for (const item of manifest.files) {
    const path = remote ? null : join(dirname(resolve(source)), item.file);
    if (!remote && !(await stat(path))?.isFile()) throw new Error('Local asset must be a regular file, not a symlink');
    const bytes = remote ? await download(new URL(item.file, url)) : await readFile(path);
    if (hash(bytes) !== item.sha256) throw new Error(`SHA-256 mismatch: ${item.file}`);
    const destination = join(folder, item.file);
    const existing = await stat(destination);
    if (existing && (!existing.isFile() || hash(await readFile(destination)) !== item.sha256)) throw new Error(`Refusing conflicting static file: ${item.file}`);
    staged.push({ destination, bytes, exists: Boolean(existing) });
  }
  // Verify the whole release and all destinations before creating any project files.
  await mkdir(folder, { recursive: true });
  for (const item of staged) if (!item.exists) await writeFile(item.destination, item.bytes, { flag: 'wx' });
  console.log('Verified five fonts and fonts.css in public/fonts/adtechui. Link /fonts/adtechui/fonts.css (include your deployment base path).');
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  installFonts(process.argv.slice(2)).catch(error => {
    console.error(`Font installation failed: ${error.message}`);
    process.exitCode = 1;
  });
}
