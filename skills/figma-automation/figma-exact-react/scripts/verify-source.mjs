#!/usr/bin/env node

import { existsSync, readFileSync, readdirSync, statSync } from 'node:fs'
import { dirname, extname, join, resolve } from 'node:path'

function parseArgs(argv) {
  const result = {}
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index]
    if (!key.startsWith('--')) continue
    const value = argv[index + 1] && !argv[index + 1].startsWith('--') ? argv[++index] : true
    result[key.slice(2)] = value
  }
  return result
}

function walk(directory, output = []) {
  for (const name of readdirSync(directory)) {
    if (['node_modules', 'dist', 'build', 'coverage', 'test-results', 'playwright-report', '.git'].includes(name)) continue
    const path = join(directory, name)
    const stats = statSync(path)
    if (stats.isDirectory()) walk(path, output)
    else if (['.js', '.jsx', '.ts', '.tsx', '.css', '.scss', '.html', '.json'].includes(extname(name))) output.push(path)
  }
  return output
}

const args = parseArgs(process.argv.slice(2))
const root = resolve(String(args.root || process.cwd()))
const source = resolve(root, String(args.source || 'src'))
const publicDirectory = resolve(root, String(args.public || 'public'))
if (!existsSync(root) || !statSync(root).isDirectory()) throw new Error(`Root directory does not exist: ${root}`)
if (!existsSync(resolve(root, 'package.json'))) throw new Error(`package.json does not exist in root: ${root}`)
if (!existsSync(source) || !statSync(source).isDirectory()) throw new Error(`Source directory does not exist: ${source}`)
if (args.public && (!existsSync(publicDirectory) || !statSync(publicDirectory).isDirectory())) throw new Error(`Explicit public directory does not exist: ${publicDirectory}`)
const files = walk(source)
if (files.length === 0) throw new Error(`No auditable source files found in: ${source}`)
const findings = []
const findingKeys = new Set()
const standaloneUnicodeIcon = />\s*[←→‹›♥♡★☆⚙✓✔✕✖⌄⌃]\s*</u
const cssUnicodeIcon = /content\s*:\s*["'][←→‹›♥♡★☆⚙✓✔✕✖⌄⌃]["']/u
const allowInlineSvgFiles = new Set(String(args['allow-inline-svg-files'] || '').split(',').map(value => value.trim()).filter(Boolean))
const allowDataImageFiles = new Set(String(args['allow-data-image-files'] || '').split(',').map(value => value.trim()).filter(Boolean))

function localAssetPath(file, reference) {
  const clean = reference.split(/[?#]/)[0]
  if (!clean || /^(?:https?:|data:|#)/i.test(clean)) return null
  if (clean.startsWith('/')) return resolve(publicDirectory, clean.slice(1))
  if (clean.startsWith('.')) return resolve(dirname(file), clean)
  return null
}

for (const file of files) {
  const text = readFileSync(file, 'utf8')
  const relative = file.slice(root.length + 1)
  const add = (rule, message) => {
    const key = `${relative}\u0000${rule}\u0000${message}`
    if (findingKeys.has(key)) return
    findingKeys.add(key)
    findings.push({ file: relative, rule, message })
  }

  if (!allowInlineSvgFiles.has(relative) && (/<svg\b/i.test(text) || /<path\b/i.test(text))) add('authored-vector', 'Inline SVG/path markup found; use the exact exported asset or an existing verified icon component.')
  if (!args['allow-unicode-icons'] && (standaloneUnicodeIcon.test(text) || cssUnicodeIcon.test(text))) add('unicode-icon', 'Standalone Unicode icon glyph found; replace it with the exact asset.')
  if (/https?:\/\/[^'"\s)]*\/api\/mcp\/asset\//i.test(text)) add('expiring-asset', 'Temporary Figma MCP asset URL remains in source.')
  if (!allowDataImageFiles.has(relative) && /data:image\//i.test(text)) add('embedded-image', 'Embedded data image found; commit the original exported asset as a file.')
  if (/(?:src=|background(?:-image)?\s*:)[^\n]*(?:screenshot|mockup|figma-reference|reference-screen)[^\n]*\.(?:png|jpe?g|webp)/i.test(text)) {
    add('screenshot-shell', 'A reference/screenshot-like image appears in rendered source; verify the UI is not a screenshot shell.')
  }

  const assetPatterns = [
    /["']([^"']+\.(?:png|jpe?g|webp|gif|svg|woff2?|ttf|otf)(?:[?#][^"']*)?)["']/gi,
    /(?:src|href)\s*=\s*["']([^"']+\.(?:png|jpe?g|webp|gif|svg|woff2?|ttf|otf)(?:[?#][^"']*)?)["']/gi,
    /url\(\s*["']?([^"')]+\.(?:png|jpe?g|webp|gif|svg|woff2?|ttf|otf)(?:[?#][^"')]+)?)['"]?\s*\)/gi,
    /(?:from|import)\s*\(?\s*["']([^"']+\.(?:png|jpe?g|webp|gif|svg|woff2?|ttf|otf)(?:[?#][^"']*)?)["']/gi,
    /new\s+URL\(\s*["']([^"']+\.(?:png|jpe?g|webp|gif|svg|woff2?|ttf|otf)(?:[?#][^"']*)?)["']/gi,
  ]
  for (const pattern of assetPatterns) for (const match of text.matchAll(pattern)) {
    const assetPath = localAssetPath(file, match[1])
    if (assetPath && !existsSync(assetPath)) add('missing-asset', `Local asset does not exist: ${match[1]}`)
  }
}

const result = { root, source, scannedFiles: files.length, passed: findings.length === 0, findings }
process.stdout.write(`${JSON.stringify(result, null, 2)}\n`)
if (!result.passed) process.exitCode = 1
