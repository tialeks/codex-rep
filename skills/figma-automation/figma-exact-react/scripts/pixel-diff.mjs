#!/usr/bin/env node

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { dirname, resolve } from 'node:path'

function parseArgs(argv) {
  const result = {}
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index]
    if (!key.startsWith('--')) continue
    result[key.slice(2)] = argv[index + 1] && !argv[index + 1].startsWith('--') ? argv[++index] : true
  }
  return result
}

function parseRegions(input) {
  if (!input) throw new Error('Missing --regions. Provide critical rectangles as name:x:y:width:height.')
  return String(input).split(',').map(value => {
    const parts = value.split(':')
    if (parts.length !== 5) throw new Error(`Invalid region format: ${value}. Expected name:x:y:width:height.`)
    const [name, x, y, width, regionHeight] = parts
    return { name, x: Number(x), y: Number(y), width: Number(width), height: Number(regionHeight) }
  })
}

function ignoreCorners(reference, actual, radius) {
  if (!radius) return
  const centers = [[radius, radius], [reference.width - radius, radius], [radius, reference.height - radius], [reference.width - radius, reference.height - radius]]
  for (let y = 0; y < reference.height; y += 1) {
    for (let x = 0; x < reference.width; x += 1) {
      if (!((x < radius || x >= reference.width - radius) && (y < radius || y >= reference.height - radius))) continue
      const outside = centers.some(([cx, cy]) => Math.abs(x - cx) <= radius && Math.abs(y - cy) <= radius && Math.hypot(x - cx, y - cy) > radius)
      if (!outside) continue
      const offset = (y * reference.width + x) * 4
      actual.data.copy(reference.data, offset, offset, offset + 4)
    }
  }
}

const args = parseArgs(process.argv.slice(2))
for (const required of ['reference', 'actual', 'diff', 'result', 'regions']) if (!args[required]) throw new Error(`Missing --${required}`)
const root = resolve(String(args.root || process.cwd()))
const referencePath = resolve(String(args.reference))
const actualPath = resolve(String(args.actual))
const diffPath = resolve(String(args.diff))
const resultPath = resolve(String(args.result))
const artifactPaths = [referencePath, actualPath, diffPath, resultPath]
if (new Set(artifactPaths).size !== artifactPaths.length) throw new Error('Reference, actual, diff, and result must use four distinct file paths.')
const requireFromProject = createRequire(resolve(root, 'package.json'))
let pixelmatchModule
let PNG
try {
  pixelmatchModule = requireFromProject('pixelmatch')
  ;({ PNG } = requireFromProject('pngjs'))
} catch {
  throw new Error('Missing pixel diff dependencies in target project. Install: npm install --save-dev --save-exact pixelmatch@7.2.0 pngjs@7.0.0')
}
const pixelmatch = pixelmatchModule.default || pixelmatchModule
const reference = PNG.sync.read(readFileSync(referencePath))
const actual = PNG.sync.read(readFileSync(actualPath))
if (reference.width !== actual.width || reference.height !== actual.height) {
  throw new Error(`Image dimensions differ: reference ${reference.width}x${reference.height}, actual ${actual.width}x${actual.height}`)
}
const threshold = Number(args.threshold || 0.1)
const maxRatio = Number(args['max-ratio'] || 0.04)
const maxRegionRatio = Number(args['max-region-ratio'] || 0.05)
const cornerRadius = Number(args['ignore-corner-radius'] || 0)
for (const [name, value] of [['threshold', threshold], ['max-ratio', maxRatio], ['max-region-ratio', maxRegionRatio]]) {
  if (!Number.isFinite(value) || value < 0 || value >= 1) throw new Error(`Invalid --${name}: ${value}. Expected 0 <= value < 1.`)
}
if (!Number.isInteger(cornerRadius) || cornerRadius < 0 || cornerRadius > Math.min(reference.width, reference.height) / 2) throw new Error(`Invalid --ignore-corner-radius: ${cornerRadius}`)
ignoreCorners(reference, actual, cornerRadius)

const diff = new PNG({ width: reference.width, height: reference.height })
const changed = pixelmatch(reference.data, actual.data, diff.data, reference.width, reference.height, { threshold, includeAA: false })
const parsedRegions = parseRegions(args.regions)
if (new Set(parsedRegions.map(region => region.name)).size !== parsedRegions.length) throw new Error('Region names in --regions must be unique.')
const regions = parsedRegions.map(region => {
  if (!region.name || !Number.isInteger(region.x) || !Number.isInteger(region.y) || !Number.isInteger(region.width) || !Number.isInteger(region.height) || region.x < 0 || region.y < 0 || region.width <= 0 || region.height <= 0 || region.x + region.width > reference.width || region.y + region.height > reference.height) {
    throw new Error(`Invalid region: ${JSON.stringify(region)}`)
  }
  const referenceCrop = new PNG({ width: region.width, height: region.height })
  const actualCrop = new PNG({ width: region.width, height: region.height })
  PNG.bitblt(reference, referenceCrop, region.x, region.y, region.width, region.height, 0, 0)
  PNG.bitblt(actual, actualCrop, region.x, region.y, region.width, region.height, 0, 0)
  const regionChanged = pixelmatch(referenceCrop.data, actualCrop.data, null, region.width, region.height, { threshold, includeAA: false })
  const ratio = regionChanged / (region.width * region.height)
  return { ...region, changedPixels: regionChanged, ratio, underThreshold: ratio <= maxRegionRatio }
})
const ratio = changed / (reference.width * reference.height)
const result = { width: reference.width, height: reference.height, threshold, maxRatio, maxRegionRatio, changedPixels: changed, ratio, regions, underThreshold: ratio <= maxRatio && regions.every(region => region.underThreshold) }
mkdirSync(dirname(diffPath), { recursive: true })
mkdirSync(dirname(resultPath), { recursive: true })
writeFileSync(diffPath, PNG.sync.write(diff))
writeFileSync(resultPath, JSON.stringify(result, null, 2))
process.stdout.write(`${JSON.stringify(result, null, 2)}\n`)
if (!result.underThreshold) process.exitCode = 1
