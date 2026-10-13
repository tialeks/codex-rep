import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, readdir, rm, symlink, writeFile } from 'node:fs/promises';
import { createHash, randomBytes } from 'node:crypto';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
import test from 'node:test';
import { installFonts } from './install-fonts.mjs';

// Byte fixtures exercise transport and integrity, not font rendering.
const filenames = ['fonts.css', 'YS-Text-Regular.woff2', 'YS-Text-Medium.woff2', 'YS-Text-Bold.ttf', 'YS-Text-Cond-Black.ttf', 'YSCompressed-VF.woff2'];
async function fixture(t) {
  const root = await mkdtemp(join(tmpdir(), 'adtechui-fonts-'));
  t.after(() => rm(root, { recursive: true, force: true }));
  const project = join(root, 'consumer with spaces');
  await mkdir(project);
  await writeFile(join(project, 'package.json'), '{}');
  await mkdir(join(root, 'fonts'));
  const manifest = { schemaVersion: 1, files: [] };
  for (const file of filenames) {
    const bytes = Buffer.from(`installer test fixture: ${file}\n`);
    await writeFile(join(root, 'fonts', file), bytes);
    manifest.files.push({ file, sha256: createHash('sha256').update(bytes).digest('hex') });
  }
  const manifestPath = join(root, 'fonts/manifest.json');
  await writeFile(manifestPath, JSON.stringify(manifest));
  return {
    root, project, manifest, manifestPath,
    save: () => writeFile(manifestPath, JSON.stringify(manifest)),
    run: (url = manifestPath) => installFonts(['--manifest', url, '--project', join(project, 'package.json')]),
    unchanged: async () => assert.deepEqual(await readdir(project), ['package.json']),
  };
}

test('help shows the optional production manifest without accessing project or network', async t => {
  const log = t.mock.method(console, 'log', () => {});
  t.mock.method(globalThis, 'fetch', () => assert.fail('help must not access the network'));
  await installFonts(['--help']);
  const output = log.mock.calls[0].arguments[0];
  assert.ok(output.includes('https://s3.mds.yandex.net/plus-ultra-storybook/components/fonts/manifest.json'));
  assert.match(output, /\[--manifest /);
});

test('fixture bytes install locally and repeat without project metadata changes', async t => {
  const f = await fixture(t);
  await f.run();
  await f.run();
  for (const { file } of f.manifest.files) assert.deepEqual(await readFile(join(f.project, 'public/fonts/adtechui', file)), await readFile(join(f.root, 'fonts', file)));
  assert.equal(await readFile(join(f.project, 'package.json'), 'utf8'), '{}');
});

for (const file of ['../fonts.css', '/fonts.css', '..\\fonts.css', '%2e%2e/fonts.css', 'fonts.css?x', 'https://example.invalid/fonts.css']) {
  test(`reject unsafe filename ${file} before writes`, async t => {
    const f = await fixture(t);
    f.manifest.files[0].file = file;
    await f.save();
    await assert.rejects(f.run(), /filename/);
    await f.unchanged();
  });
}

for (const mutation of ['duplicate', 'missing', 'hash', 'hash-newline', 'schema', 'corruption']) {
  test(`reject ${mutation} before writes`, async t => {
    const f = await fixture(t);
    if (mutation === 'duplicate') f.manifest.files[0] = f.manifest.files[1];
    if (mutation === 'missing') f.manifest.files.pop();
    if (mutation === 'hash') f.manifest.files[0].sha256 = 'invalid';
    if (mutation === 'hash-newline') f.manifest.files[0].sha256 += '\n';
    if (mutation === 'schema') f.manifest.schemaVersion = 2;
    if (mutation === 'corruption') await writeFile(join(f.root, 'fonts/fonts.css'), 'corrupted');
    await f.save();
    await assert.rejects(f.run());
    await f.unchanged();
  });
}

for (const path of ['public', 'public/fonts', 'public/fonts/adtechui', 'public/fonts/adtechui/fonts.css']) {
  test(`reject destination symlink ${path}`, async t => {
    const f = await fixture(t);
    const parent = path.split('/').slice(0, -1).join('/');
    await mkdir(join(f.project, parent), { recursive: true });
    await symlink(join(f.root, 'fonts'), join(f.project, path));
    await assert.rejects(f.run(), /symlink|conflicting/);
  });
}

test('refuse conflicting existing file without installing other files', async t => {
  const f = await fixture(t);
  const folder = join(f.project, 'public/fonts/adtechui');
  await mkdir(folder, { recursive: true });
  await writeFile(join(folder, 'fonts.css'), 'keep me');
  await assert.rejects(f.run(), /conflicting/);
  assert.deepEqual(await readdir(folder), ['fonts.css']);
  assert.equal(await readFile(join(folder, 'fonts.css'), 'utf8'), 'keep me');
});

for (const url of ['http://example.invalid/manifest.json', 'file:///manifest.json', 'https://example.invalid/manifest.json#fragment']) {
  test(`reject non-approved URL form ${new URL(url).protocol}`, async t => {
    const f = await fixture(t);
    await assert.rejects(f.run(url), /HTTPS/);
    await f.unchanged();
  });
}

for (const field of ['username', 'password']) {
  test(`reject URL with ${field} before any network request`, async t => {
    const f = await fixture(t);
    const url = new URL('https://example.invalid/manifest.json');
    // Generated test-only userinfo; no embedded credential or external request.
    url[field] = randomBytes(12).toString('hex');
    t.mock.method(globalThis, 'fetch', () => assert.fail('credentials must be rejected before fetch'));
    await assert.rejects(f.run(url.href), /HTTPS/);
    await f.unchanged();
  });
}

test('HTTPS resolves six fixture assets relative to manifest and enforces fetch policy', async t => {
  const f = await fixture(t);
  const urls = [];
  t.mock.method(globalThis, 'fetch', async (url, options) => {
    assert.equal(options.redirect, 'error');
    assert.ok(options.signal instanceof AbortSignal);
    urls.push(String(url));
    return new Response(await readFile(join(f.root, 'fonts', url.pathname.split('/').at(-1))));
  });
  await f.run('https://example.invalid/components/fonts/manifest.json');
  assert.deepEqual(urls, ['manifest.json', ...f.manifest.files.map(item => item.file)].map(file => `https://example.invalid/components/fonts/${file}`));
  urls.length = 0;
  await installFonts(['--project', join(f.project, 'package.json')]);
  assert.deepEqual(urls, ['manifest.json', ...f.manifest.files.map(item => item.file)].map(file => `https://s3.mds.yandex.net/plus-ultra-storybook/components/fonts/${file}`));
  for (const { file } of f.manifest.files) assert.deepEqual(await readFile(join(f.project, 'public/fonts/adtechui', file)), await readFile(join(f.root, 'fonts', file)));
});

for (const status of [302, 404, 500]) {
  test(`HTTP ${status} leaves project unchanged`, async t => {
    const f = await fixture(t);
    t.mock.method(globalThis, 'fetch', async () => new Response('', { status }));
    await assert.rejects(f.run('https://example.invalid/fonts/manifest.json'), /Download failed/);
    await f.unchanged();
  });
}

test('late HTTPS transport failure leaves project unchanged', async t => {
  const f = await fixture(t);
  let requests = 0;
  t.mock.method(globalThis, 'fetch', async url => {
    if (++requests === 7) throw new Error('network interrupted');
    return new Response(await readFile(join(f.root, 'fonts', url.pathname.split('/').at(-1))));
  });
  await assert.rejects(f.run('https://example.invalid/fonts/manifest.json'), /network interrupted/);
  await f.unchanged();
});
