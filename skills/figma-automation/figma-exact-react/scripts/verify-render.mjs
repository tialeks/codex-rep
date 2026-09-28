#!/usr/bin/env node

import { mkdirSync, writeFileSync } from 'node:fs'
import { createRequire } from 'node:module'
import { basename, resolve } from 'node:path'

function parseArgs(argv) {
  const result = {}
  for (let index = 0; index < argv.length; index += 1) {
    const key = argv[index]
    if (!key.startsWith('--')) continue
    result[key.slice(2)] = argv[index + 1] && !argv[index + 1].startsWith('--') ? argv[++index] : true
  }
  return result
}

function parseFontContract(input) {
  if (!input) throw new Error('Missing --font-contract. Use Family=/font/file.ttf|/font/other.ttf;System Family')
  return String(input).split(';').map(value => {
    const [familyPart, filesPart, ...extra] = value.split('=')
    const family = familyPart?.trim()
    if (!family || extra.length > 0) throw new Error(`Invalid font contract entry: ${value}`)
    const files = filesPart === undefined ? [] : filesPart.split('|').map(file => file.trim()).filter(Boolean)
    return { family, files }
  })
}

const args = parseArgs(process.argv.slice(2))
const root = resolve(String(args.root || process.cwd()))
const url = String(args.url || '')
if (!url) throw new Error('Missing --url')
const rawWidths = String(args.widths || '').split(',').filter(Boolean)
const widths = rawWidths.map(Number)
const height = Number(args.height || 900)
const out = resolve(String(args.out || '/tmp/figma-exact-render'))
const pageSelector = args['page-selector'] ? String(args['page-selector']) : ''
const readySelector = args['ready-selector'] ? String(args['ready-selector']) : ''
if (!pageSelector) throw new Error('Missing --page-selector')
if (!readySelector) throw new Error('Missing --ready-selector')
if (widths.length === 0 || widths.some(width => !Number.isInteger(width) || width <= 0) || new Set(widths).size !== widths.length) throw new Error(`Invalid --widths: ${args.widths || ''}`)
if (!Number.isInteger(height) || height <= 0) throw new Error(`Invalid --height: ${args.height || ''}`)
const stickySelector = args['sticky-selector'] ? String(args['sticky-selector']) : null
const statusSelector = args['status-selector'] ? String(args['status-selector']) : null
const fontContract = parseFontContract(args['font-contract'])
if (new Set(fontContract.map(item => item.family)).size !== fontContract.length) throw new Error('Duplicate family in --font-contract.')
const expectedFonts = fontContract.map(item => item.family)
const systemFonts = new Set(String(args['system-fonts'] || '').split(',').map(value => value.trim()).filter(Boolean))
if (Array.from(systemFonts).some(font => !expectedFonts.includes(font))) throw new Error('--system-fonts must be a subset of the families declared in --font-contract.')
for (const item of fontContract) {
  if (systemFonts.has(item.family) && item.files.length > 0) throw new Error(`System font must not declare files in --font-contract: ${item.family}`)
  if (!systemFonts.has(item.family) && item.files.length === 0) throw new Error(`Non-system font must declare at least one file in --font-contract: ${item.family}`)
}
const allowCoveringMedia = new Set(String(args['allow-covering-media'] || '').split(',').map(value => value.trim()).filter(Boolean))
const scrollY = Number(args['scroll-y'] || 320)
mkdirSync(out, { recursive: true })

const requireFromProject = createRequire(resolve(root, 'package.json'))
let chromium
try {
  ;({ chromium } = requireFromProject('@playwright/test'))
} catch {
  try {
    ;({ chromium } = requireFromProject('playwright'))
  } catch {
    throw new Error('Missing Playwright in target project. Install exact dev dependency: npm install --save-dev --save-exact @playwright/test@1.62.1')
  }
}

const browser = await chromium.launch({ headless: true })
const results = []

try {
  for (const width of widths) {
    const page = await browser.newPage({ viewport: { width, height }, deviceScaleFactor: 1 })
    const errors = []
    const failedRequests = []
    page.on('console', message => {
      if (message.type() === 'error') errors.push(`console: ${message.text()}`)
    })
    page.on('pageerror', error => errors.push(`pageerror: ${error.message}`))
    page.on('requestfailed', request => failedRequests.push(`${request.method()} ${request.url()}: ${request.failure()?.errorText || 'failed'}`))
    page.on('response', response => {
      if (response.status() >= 400) failedRequests.push(`${response.status()} ${response.url()}`)
    })
    const response = await page.goto(url, { waitUntil: 'domcontentloaded' })
    await page.locator(readySelector).waitFor({ state: 'visible' })
    await page.evaluate(async () => {
      await document.fonts.ready
      await Promise.all(Array.from(document.images, image => image.decode().catch(() => undefined)))
      await new Promise(requestAnimationFrame)
      await new Promise(requestAnimationFrame)
    })

    const runtime = await page.evaluate(({ selector, fontContracts, systemFontFamilies, allowedCoveringMedia }) => {
      const text = document.body.innerText.replace(/\s+/g, ' ').trim()
      const brokenImages = Array.from(document.images)
        .filter(image => !image.complete || image.naturalWidth === 0)
        .map(image => image.currentSrc || image.getAttribute('src'))
      const overlay = Boolean(document.querySelector('vite-error-overlay, nextjs-portal, [data-nextjs-dialog-overlay]'))
      const pageElement = document.querySelector(selector)
      const pageBox = pageElement?.getBoundingClientRect() ?? null
      const candidates = Array.from(document.querySelectorAll('*'))
      const coveringMedia = candidates.flatMap(element => {
        const rect = element.getBoundingClientRect()
        const covers = rect.width >= innerWidth * .9 && rect.height >= innerHeight * .9 && rect.width * rect.height >= innerWidth * innerHeight * .85
        const identity = element.id ? `#${element.id}` : element.classList.length ? `.${Array.from(element.classList).join('.')}` : element.tagName.toLowerCase()
        if (!covers) return []
        const entries = []
        const style = getComputedStyle(element)
        if (['IMG', 'CANVAS', 'VIDEO'].includes(element.tagName) || style.backgroundImage !== 'none') {
          entries.push({ identity, tag: element.tagName, width: rect.width, height: rect.height, backgroundImage: style.backgroundImage })
        }
        for (const pseudo of ['::before', '::after']) {
          const pseudoStyle = getComputedStyle(element, pseudo)
          if (pseudoStyle.content !== 'none' && pseudoStyle.backgroundImage !== 'none') {
            entries.push({ identity: `${identity}${pseudo}`, tag: pseudo, width: rect.width, height: rect.height, backgroundImage: pseudoStyle.backgroundImage })
          }
        }
        return entries.filter(entry => !allowedCoveringMedia.includes(entry.identity))
      })
      const normalizeFamily = value => value.replace(/["']/g, '').trim()
      const fontFaces = Array.from(document.fonts).map(face => ({ family: normalizeFamily(face.family), status: face.status, weight: face.weight, stretch: face.stretch, style: face.style }))
      const resourceUrls = performance.getEntriesByType('resource').map(entry => entry.name)
      const declaredFontSources = []
      for (const sheet of Array.from(document.styleSheets)) {
        let rules = []
        try { rules = Array.from(sheet.cssRules) } catch { continue }
        for (const rule of rules) {
          if (rule.type !== CSSRule.FONT_FACE_RULE) continue
          const family = normalizeFamily(rule.style.getPropertyValue('font-family'))
          const src = rule.style.getPropertyValue('src')
          const sources = Array.from(src.matchAll(/url\(\s*["']?([^"')]+)["']?\s*\)/g), match => new URL(match[1], location.href).pathname)
          declaredFontSources.push({ family, sources })
        }
      }
      const fontsLoaded = fontContracts.map(contract => {
        const isSystem = systemFontFamilies.includes(contract.family)
        const matchingFaces = fontFaces.filter(face => face.family === contract.family)
        const declaredSources = declaredFontSources.filter(face => face.family === contract.family).flatMap(face => face.sources)
        const files = contract.files.map(file => ({
          file,
          declared: declaredSources.some(source => source.endsWith(file)),
          loaded: resourceUrls.some(url => new URL(url, location.href).pathname.endsWith(file)),
        }))
        const faceLoaded = isSystem ? document.fonts.check(`16px "${contract.family}"`) : matchingFaces.some(face => face.status === 'loaded')
        return { font: contract.family, system: isSystem, faceLoaded, files, loaded: faceLoaded && files.every(file => file.declared && file.loaded), faces: matchingFaces }
      })
      return {
        title: document.title,
        meaningfulText: text.length >= 10,
        brokenImages,
        frameworkOverlay: overlay,
        horizontalOverflow: Math.max(0, document.documentElement.scrollWidth - innerWidth),
        pageBox: pageBox ? { width: pageBox.width, left: pageBox.left, right: pageBox.right } : null,
        coveringMedia,
        fontsLoaded,
      }
    }, { selector: pageSelector, fontContracts: fontContract, systemFontFamilies: Array.from(systemFonts), allowedCoveringMedia: Array.from(allowCoveringMedia) })

    const initialScreenshot = resolve(out, `initial-${width}x${height}.png`)
    await page.screenshot({ path: initialScreenshot, fullPage: true, animations: 'disabled' })

    let sticky = null
    let scrolledScreenshot = null
    if (stickySelector || statusSelector) {
      await page.evaluate(value => window.scrollTo(0, value), scrollY)
      await page.waitForTimeout(80)
      sticky = await page.evaluate(({ header, status }) => {
        const metrics = selector => {
          if (!selector) return null
          const element = document.querySelector(selector)
          if (!element) return null
          const rect = element.getBoundingClientRect()
          return { top: rect.top, background: getComputedStyle(element).backgroundColor }
        }
        return { header: metrics(header), status: metrics(status), scrollY: window.scrollY }
      }, { header: stickySelector, status: statusSelector })
      scrolledScreenshot = resolve(out, `scrolled-${width}x${height}.png`)
      await page.screenshot({ path: scrolledScreenshot, fullPage: false, animations: 'disabled' })
    }

    const checks = {
      responseOk: Boolean(response && response.ok()),
      meaningfulText: runtime.meaningfulText,
      noBrokenImages: runtime.brokenImages.length === 0,
      noFrameworkOverlay: !runtime.frameworkOverlay,
      noConsoleErrors: errors.length === 0,
      noFailedRequests: failedRequests.length === 0,
      noPageOverflow: runtime.horizontalOverflow === 0,
      pageSelectorResolved: Boolean(runtime.pageBox),
      pageFitsViewport: Boolean(runtime.pageBox && runtime.pageBox.width <= width + 0.5 && runtime.pageBox.left >= -0.5 && runtime.pageBox.right <= width + 0.5),
      noViewportCoveringMedia: runtime.coveringMedia.length === 0,
      expectedFontsLoaded: runtime.fontsLoaded.every(item => item.loaded),
      stickyHeaderFixed: !stickySelector || (sticky?.scrollY > 0 && sticky.header !== null && Math.abs(sticky.header.top) <= 1),
      statusBarFixed: !statusSelector || (sticky?.scrollY > 0 && sticky.status !== null && Math.abs(sticky.status.top) <= 1),
    }
    results.push({ width, height, url: page.url(), status: response?.status() ?? null, screenshots: { initial: basename(initialScreenshot), scrolled: scrolledScreenshot ? basename(scrolledScreenshot) : null }, runtime, sticky, errors, failedRequests, checks, passed: Object.values(checks).every(Boolean) })
    await page.close()
  }
} finally {
  await browser.close()
}

const report = { passed: results.every(result => result.passed), results }
writeFileSync(resolve(out, 'report.json'), JSON.stringify(report, null, 2))
process.stdout.write(`${JSON.stringify(report, null, 2)}\n`)
if (!report.passed) process.exitCode = 1
