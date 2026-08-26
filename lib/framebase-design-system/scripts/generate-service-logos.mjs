import { mkdir, writeFile } from "node:fs/promises"
import { fileURLToPath } from "node:url"
import path from "node:path"

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "..")
const outputDir = path.join(root, "public", "service-logos")
const loaderDir = path.join(outputDir, "loader-marks")

const palettes = [
  ["#2867EB", "#77A6F6"], ["#6554E3", "#A192F4"], ["#9D4BD2", "#D691ED"],
  ["#D43C8B", "#F486B5"], ["#DF4C58", "#F58F85"], ["#E56C28", "#F4AF6B"],
  ["#C58E14", "#EFD05F"], ["#68A525", "#AFD773"], ["#249B58", "#76D497"],
  ["#07927E", "#68CEBF"], ["#118BB5", "#71C9E5"], ["#3975C7", "#8DB5EA"],
  ["#5D6682", "#A4ABBC"], ["#8153C2", "#BD94E6"], ["#BE4A70", "#EA91AA"],
  ["#C96A49", "#EEA688"], ["#3C9A89", "#8BD4C5"], ["#2D8E9A", "#7AC9D1"],
  ["#895A98", "#C19CCA"], ["#4A7B67", "#92BEAA"],
]

const mixHex = (from, to, amount) => {
  const parse = color => color.slice(1).match(/.{2}/g).map(value => Number.parseInt(value, 16))
  const a = parse(from)
  const b = parse(to)
  return `#${a.map((value, index) => Math.round(value + (b[index] - value) * amount).toString(16).padStart(2, "0")).join("")}`
}

const stroke = (body, width = 3.6) => `<g fill="none" stroke="#fff" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round">${body}</g>`
const fill = body => `<g fill="#fff">${body}</g>`

const organicPath = ({ cx = 32, cy = 32, radius, amplitude, lobes, phase = 0, points = 96 }) => {
  const coords = Array.from({ length: points }, (_, point) => {
    const angle = phase + point / points * Math.PI * 2
    const r = radius + Math.sin(angle * lobes) * amplitude
    return [cx + Math.cos(angle) * r, cy + Math.sin(angle) * r]
  })
  return `${coords.map(([x, y], point) => `${point ? "L" : "M"}${x.toFixed(2)} ${y.toFixed(2)}`).join("")}Z`
}

const abstractSymbol = index => {
  const seed = index + 1
  const family = index % 10
  const phase = (seed % 7) * .19
  const outerLobes = 6 + seed % 7
  const innerLobes = 4 + seed % 5
  const outer = organicPath({ radius: 15.1 + seed % 3 * .35, amplitude: 1.65 + seed % 4 * .18, lobes: outerLobes, phase })
  const inner = organicPath({ radius: 7.2 + seed % 3 * .5, amplitude: 1.05 + seed % 4 * .17, lobes: innerLobes, phase: phase + .37 })

  if (family === 0) {
    return `${stroke(`<path d="${outer}"/>`, 5.1)}${fill(`<path d="${inner}"/>`)}`
  }

  if (family === 1) {
    const petals = 5 + seed % 4
    const petalShapes = Array.from({ length: petals }, (_, petal) => {
      const angle = petal / petals * 360 + seed * 7
      return `<ellipse cx="32" cy="20.2" rx="${(5.1 + seed % 3 * .35).toFixed(2)}" ry="${(9.5 + seed % 2 * .8).toFixed(2)}" transform="rotate(${angle.toFixed(2)} 32 32)"/>`
    }).join("")
    const core = organicPath({ radius: 6.5, amplitude: 1.1 + seed % 3 * .25, lobes: 5 + seed % 4, phase })
    return `${fill(petalShapes)}${fill(`<path d="${core}"/>`)}`
  }

  if (family === 2) {
    const tilt = 24 + seed % 5 * 8
    const nucleus = organicPath({ radius: 6.3 + seed % 3 * .4, amplitude: 1.1, lobes: 5 + seed % 4, phase })
    return `${stroke(`<ellipse cx="32" cy="32" rx="18" ry="9.2" transform="rotate(${tilt} 32 32)"/><ellipse cx="32" cy="32" rx="18" ry="9.2" transform="rotate(${-tilt} 32 32)"/>`, 4.2)}${fill(`<path d="${nucleus}"/>`)}`
  }

  if (family === 3) {
    const clover = Array.from({ length: 4 }, (_, petal) => `<ellipse cx="32" cy="23" rx="6.4" ry="9.8" transform="rotate(${petal * 90 + seed % 3 * 6} 32 32)"/>`).join("")
    return `${stroke(clover, 4.1)}${fill('<circle cx="32" cy="32" r="4.3"/>')}`
  }

  if (family === 4) {
    const rotation = seed % 2 ? 0 : 90
    const ribbon = "M16 32C20 20 26 20 32 32S44 44 48 32C44 20 38 20 32 32S20 44 16 32"
    return stroke(`<path d="${ribbon}" transform="rotate(${rotation} 32 32)"/>`, 5)
  }

  if (family === 5) {
    const middle = organicPath({ radius: 10.2, amplitude: 1.15, lobes: 5 + seed % 4, phase: phase + .45 })
    return `${stroke(`<path d="${outer}"/>`, 4.4)}${stroke(`<path d="${middle}"/>`, 3.2)}${fill('<circle cx="32" cy="32" r="3.2"/>')}`
  }

  if (family === 6) {
    const petals = Array.from({ length: 3 }, (_, petal) => `<ellipse cx="32" cy="23" rx="6.2" ry="11" transform="rotate(${petal * 120 + seed % 4 * 9} 32 32)"/>`).join("")
    return `${fill(petals)}${fill('<circle cx="32" cy="32" r="4.1"/>')}`
  }

  if (family === 7) {
    const seedShape = organicPath({ radius: 6.2, amplitude: 1, lobes: 4 + seed % 3, phase })
    return `${stroke('<rect x="19" y="19" width="26" height="26" rx="8" transform="rotate(45 32 32)"/>', 4.8)}${fill(`<path d="${seedShape}"/>`)}`
  }

  if (family === 8) {
    const satellites = Array.from({ length: 3 }, (_, point) => {
      const angle = phase + point / 3 * Math.PI * 2
      const x = 32 + Math.cos(angle) * 15.2
      const y = 32 + Math.sin(angle) * 15.2
      return `<circle cx="${x.toFixed(2)}" cy="${y.toFixed(2)}" r="3.1"/>`
    }).join("")
    return `${stroke('<circle cx="32" cy="32" r="15.2"/>', 3.8)}${fill(`${satellites}<circle cx="32" cy="32" r="5.2"/>`)}`
  }

  const capsules = Array.from({ length: 3 }, (_, capsule) => `<rect x="27.4" y="16" width="9.2" height="32" rx="4.6" transform="rotate(${capsule * 60 + seed % 4 * 7} 32 32)"/>`).join("")
  return `${fill(capsules)}${fill('<circle cx="32" cy="32" r="3.8"/>')}`
}

const logos = [
  ["nova", "Nova", stroke('<path d="M32 17l2.8 5.2 5.7-1.5-.3 5.9 5.4 2.3-3.4 4.8 3.4 4.8-5.4 2.3.3 5.9-5.7-1.5L32 50l-2.8-4.8-5.7 1.5.3-5.9-5.4-2.3 3.4-4.8-3.4-4.8 5.4-2.3-.3-5.9 5.7 1.5L32 17Z"/><circle cx="32" cy="33.7" r="8.5"/>', 3.1)],
  ["spark", "Spark", fill('<path d="M32 14.5 36 27l12.5 4-12.5 4L32 47.5 28 35l-12.5-4L28 27 32 14.5Z"/><circle cx="47" cy="17" r="3"/>')],
  ["orbit", "Orbit", stroke('<circle cx="32" cy="32" r="7"/><ellipse cx="32" cy="32" rx="18" ry="9" transform="rotate(28 32 32)"/><circle cx="46.5" cy="41" r="2.2" fill="#fff" stroke="none"/>')],
  ["pulse", "Pulse", stroke('<path d="M14 33h9l4-12 8 24 5-12h10"/>')],
  ["layers", "Layers", stroke('<path d="m32 16 18 9-18 9-18-9 18-9Z"/><path d="m16 33 16 8 16-8M18 41l14 7 14-7"/>', 3.2)],
  ["link", "Link", stroke('<path d="M27 38.5 23.5 42a7 7 0 0 1-10-10l7-7a7 7 0 0 1 10 0M37 25.5l3.5-3.5a7 7 0 0 1 10 10l-7 7a7 7 0 0 1-10 0M24 40l16-16"/>', 3.4)],
  ["compass", "Compass", stroke('<circle cx="32" cy="32" r="18"/><path d="m40 22-5 13-13 5 5-13 13-5Z"/><circle cx="32" cy="32" r="2" fill="#fff" stroke="none"/>', 3.2)],
  ["shield", "Shield", stroke('<path d="M32 15 47 21v10c0 10-6.2 16.5-15 20-8.8-3.5-15-10-15-20V21l15-6Z"/><path d="m25 32 5 5 10-11"/>', 3.3)],
  ["cloud", "Cloud", fill('<path d="M21.5 45h24a9 9 0 0 0 .9-18A15 15 0 0 0 18 25.3 10 10 0 0 0 21.5 45Zm3.5-9 6-6v4h9v4h-9v4l-6-6Z"/>')],
  ["wave", "Wave", stroke('<path d="M14 34c5-10 10 10 15 0s10 10 15 0 6-3 7 0M14 25c4-7 8 7 12 0s8 7 12 0 8-4 12 0M17 43c4-6 8 6 12 0s8 6 12 0"/>', 3.2)],
  ["bolt", "Bolt", fill('<path d="M35 13 18 35h12l-2 16 18-25H34l1-13Z"/>')],
  ["leaf", "Leaf", stroke('<path d="M48 16C30 16 18 25 18 38c0 6 4 10 10 10 13 0 20-14 20-32Z"/><path d="M19 47c5-9 12-16 23-23M28 38h9M34 31v-7"/>', 3.1)],
  ["pin", "Pin", stroke('<path d="M32 51s14-13 14-24a14 14 0 1 0-28 0c0 11 14 24 14 24Z"/><circle cx="32" cy="27" r="5"/>', 3.4)],
  ["chat", "Chat", fill('<path d="M15 18h34a5 5 0 0 1 5 5v17a5 5 0 0 1-5 5H30l-10 7v-7h-5a5 5 0 0 1-5-5V23a5 5 0 0 1 5-5Zm8 11a3 3 0 1 0 0 6 3 3 0 0 0 0-6Zm9 0a3 3 0 1 0 0 6 3 3 0 0 0 0-6Zm9 0a3 3 0 1 0 0 6 3 3 0 0 0 0-6Z" transform="scale(.9) translate(3.5 3.5)"/>')],
  ["grid", "Grid", stroke('<rect x="16" y="16" width="13" height="13" rx="3"/><rect x="35" y="16" width="13" height="13" rx="3"/><rect x="16" y="35" width="13" height="13" rx="3"/><rect x="35" y="35" width="13" height="13" rx="3"/>', 3.2)],
  ["infinity", "Infinity", stroke('<path d="M32 32c-5-8-9-12-14-12a10 10 0 0 0 0 20c5 0 9-4 14-12 5 8 9 12 14 12a10 10 0 0 0 0-20c-5 0-9 4-14 12Z"/>', 4)],
  ["diamond", "Diamond", stroke('<path d="m32 13 18 18-18 20-18-20 18-18Z"/><path d="m23 22 9 29 9-29M14 31h36"/>', 3)],
  ["crown", "Crown", fill('<path d="m14 21 10 8 8-15 8 15 10-8-4 25H18l-4-25Zm7 29h22v-4H21v4Z"/>')],
  ["mountain", "Mountain", stroke('<path d="m12 47 14-25 7 11 5-8 14 22H12Z"/><path d="m22 29 4 4 4-4M36 29l3 4 3-3"/>', 3.3)],
  ["bloom", "Bloom", fill('<circle cx="32" cy="32" r="6"/><ellipse cx="32" cy="20" rx="6" ry="10"/><ellipse cx="32" cy="44" rx="6" ry="10"/><ellipse cx="20" cy="32" rx="10" ry="6"/><ellipse cx="44" cy="32" rx="10" ry="6"/>')],
  ["hex", "Hex", stroke('<path d="m32 14 16 9v18l-16 9-16-9V23l16-9Z"/><path d="m25 28 7-4 7 4v8l-7 4-7-4v-8Z"/>', 3.2)],
  ["bridge", "Bridge", stroke('<path d="M14 45h36M18 45V30M46 45V30M18 31c7 0 8-12 14-12s7 12 14 12M24 28v17M40 28v17"/>', 3.2)],
  ["ribbon", "Ribbon", stroke('<path d="M24 15h16v34l-8-6-8 6V15Z"/><path d="M24 24h16"/>', 3.3)],
  ["play", "Play", `${stroke('<circle cx="32" cy="32" r="18"/>', 4)}${fill('<path d="m28 23 14 9-14 9V23Z"/>')}`],
  ["nodes", "Nodes", stroke('<path d="m21 22 22 0M21 22l11 20M43 22 32 42"/><circle cx="21" cy="22" r="6" fill="#fff"/><circle cx="43" cy="22" r="6" fill="#fff"/><circle cx="32" cy="42" r="6" fill="#fff"/>', 3)],
  ["code", "Code", stroke('<path d="m25 20-11 12 11 12M39 20l11 12-11 12M36 15l-8 34"/>', 3.7)],
  ["eye", "Eye", stroke('<path d="M12 32s7-13 20-13 20 13 20 13-7 13-20 13S12 32 12 32Z"/><circle cx="32" cy="32" r="6"/>', 3.4)],
  ["target", "Target", stroke('<circle cx="32" cy="32" r="18"/><circle cx="32" cy="32" r="10"/><circle cx="32" cy="32" r="3" fill="#fff"/><path d="m38 26 12-12M42 14h8v8"/>', 3.2)],
  ["rocket", "Rocket", fill('<path d="M44 14c-12 2-20 9-24 20l10 10c11-4 18-12 20-24l-6-6Zm-5 9a4 4 0 1 1 0 8 4 4 0 0 1 0-8ZM20 35l-7 4 8 3 3 8 4-7-8-8Z"/>')],
  ["cube", "Cube", stroke('<path d="m32 14 17 9v18l-17 9-17-9V23l17-9Z"/><path d="m15 23 17 9 17-9M32 32v18"/>', 3.2)],
  ["prism", "Prism", stroke('<path d="m32 13 19 37H13l19-37Z"/><path d="m21 35 11-22 11 22H21Z"/>', 3.1)],
  ["moon", "Moon", fill('<path d="M43 42c-14 2-24-13-17-25-9 3-14 11-13 20 2 11 12 18 23 16 7-1 12-5 15-11-2 0-5 0-8 0Z"/>')],
  ["flame", "Flame", fill('<path d="M35 12c2 11-7 13-3 23 2-5 6-7 8-12 7 7 11 15 7 23-3 7-10 10-17 8-9-2-15-11-12-20 2-7 8-11 10-19 4 4 4 9 4 12 6-5 7-10 3-15Z"/>')],
  ["key", "Key", stroke('<circle cx="23" cy="32" r="10"/><path d="M33 32h18M43 32v7M49 32v5"/>', 4)],
  ["anchor", "Anchor", stroke('<circle cx="32" cy="18" r="5"/><path d="M32 23v27M20 31h24M15 39c2 8 8 12 17 12s15-4 17-12M15 39l-2 7M49 39l2 7"/>', 3.2)],
  ["bell", "Bell", fill('<path d="M32 13a6 6 0 0 1 6 5c7 2 10 8 10 16v7l5 5H11l5-5v-7c0-8 3-14 10-16a6 6 0 0 1 6-5Zm-7 36h14c-1 4-3 6-7 6s-6-2-7-6Z"/>')],
  ["bookmark", "Bookmark", stroke('<path d="M20 14h24v37L32 43l-12 8V14Z"/><path d="M26 25h12M26 32h8"/>', 3.3)],
  ["flag", "Flag", fill('<path d="M17 13h4v40h-4V13Zm5 3h27l-7 10 7 10H22V16Z"/>')],
  ["chart", "Chart", stroke('<path d="M15 48h36M18 43l9-10 8 5 13-18"/><path d="M40 20h8v8"/>', 3.5)],
  ["wand", "Wand", stroke('<path d="m18 47 25-25 5 5-25 25-5-5ZM17 17v7M13.5 20.5h7M39 12v6M36 15h6M49 39v7M45.5 42.5h7"/>', 3)],
  ["fingerprint", "Fingerprint", stroke('<path d="M22 47c-3-6-4-12-2-19 3-9 18-10 23-2 4 7-1 15 3 20M27 50c-4-8-5-18 0-23 4-4 12-2 12 4 0 8-2 11 2 18M32 46c-2-7 2-12 1-16"/>', 3.1)],
  ["switch", "Switch", stroke('<rect x="12" y="21" width="40" height="22" rx="11"/><circle cx="39" cy="32" r="7" fill="#fff" stroke="none"/>', 3.2)],
  ["maze", "Maze", stroke('<path d="M14 23V14h36v36H32v-9h9V23H23v18h9v9H14V32h9v9M32 23v9h9"/>', 3.1)],
  ["spiral", "Spiral", stroke('<path d="M32 32c0-5 8-5 8 1 0 8-13 11-19 4-8-10 2-24 15-23 15 2 21 20 11 31-9 10-26 7-33-4"/>', 3.4)],
  ["drop", "Drop", stroke('<path d="M32 12s15 17 15 28a15 15 0 0 1-30 0c0-11 15-28 15-28Z"/><path d="M25 41c1 4 4 6 8 6"/>', 3.3)],
  ["portal", "Portal", stroke('<circle cx="32" cy="32" r="18"/><path d="M15 32h34M32 15c6 5 9 10 9 17s-3 12-9 17c-6-5-9-10-9-17s3-12 9-17Z"/>', 3)],
  ["handshake", "Together", stroke('<path d="m13 28 10-8 8 5 7-4 13 10M13 28l-2 12 8 7 5-5 5 4 5-4 5 3 10-10M24 42l-5-5M29 46l-5-5M34 42l-5-5M39 45l-5-5M31 25l-6 6c3 3 6 3 9 0l4-3"/>', 2.8)],
  ["clock", "Clock", stroke('<circle cx="32" cy="32" r="19"/><path d="M32 20v13l9 6"/>', 3.8)],
  ["star", "Star", fill('<path d="m32 12 6 13 14 2-10 10 2 15-12-7-12 7 2-15-10-10 14-2 6-13Z"/>')],
  ["knot", "Knot", stroke('<path d="M22 18a8 8 0 0 1 12 0l12 12a8 8 0 0 1-12 12L22 30a8 8 0 0 1 0-12ZM42 46a8 8 0 0 1-12 0L18 34a8 8 0 0 1 12-12l12 12a8 8 0 0 1 0 12Z"/>', 3.2)],
]

const brandTitles = [
  "Nova", "Petal", "Orbit", "Halo", "Flux", "Aster", "Mallow", "Weave", "Corona", "Loop",
  "Sol", "Clover", "Lattice", "Aura", "Twin", "Ripple", "Flora", "Mesh", "Rosette", "Bond",
  "Crest", "Bloom", "Knot", "Ember", "Runa", "Vale", "Mira", "Opal", "Sora", "Nivo",
  "Elara", "Vela", "Noma", "Lucent", "Kora", "Nami", "Taro", "Yuna", "Zori", "Filo",
  "Arca", "Ilya", "Luno", "Orin", "Piko", "Seli", "Timo", "Varo", "Welo", "Zena",
]

logos.forEach((logo, index) => { logo[1] = brandTitles[index] })

const buildSvg = ([slug, title], index) => {
  const [from, to] = palettes[index % palettes.length]
  const materialShade = mixHex(from, "#17213A", .58)
  const glyphMid = mixHex(to, "#FFFFFF", .78)
  const glyphBottom = mixHex(to, "#FFFFFF", .58)
  const lowerGlow = mixHex(to, "#FFFFFF", .42)
  const uid = `${slug}-${index + 1}`
  const squircle = "M20 .8C8.5.8.8 8.5.8 20v24c0 11.5 7.7 19.2 19.2 19.2h24c11.5 0 19.2-7.7 19.2-19.2V20C63.2 8.5 55.5.8 44 .8H20Z"
  const symbol = abstractSymbol(index)
  const body = symbol
    .replaceAll('fill="#fff"', `fill="url(#${uid}-glyph)"`)
    .replaceAll('stroke="#fff"', `stroke="url(#${uid}-glyph)"`)
    .replace(/stroke-width="([\d.]+)"/g, (_, width) => `stroke-width="${Math.min(Number(width) * 1.22, 5.1).toFixed(2)}"`)
  const gloss = symbol
    .replaceAll('fill="#fff"', `fill="url(#${uid}-glyph-gloss)"`)
    .replaceAll('stroke="#fff"', `stroke="url(#${uid}-glyph-gloss)"`)
    .replace(/stroke-width="([\d.]+)"/g, (_, width) => `stroke-width="${Math.min(Number(width) * .52, 2.2).toFixed(2)}"`)
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-labelledby="${uid}-title" overflow="visible">
  <title id="${uid}-title">${title}</title>
  <defs>
    <linearGradient id="${uid}-bg" x1="32" y1="1" x2="32" y2="63" gradientUnits="userSpaceOnUse">
      <stop stop-color="${from}"/>
      <stop offset=".48" stop-color="${from}" stop-opacity=".92"/>
      <stop offset="1" stop-color="${to}"/>
    </linearGradient>
    <radialGradient id="${uid}-top-light" cx="0" cy="0" r="1" gradientTransform="translate(20 4) rotate(65) scale(38 48)" gradientUnits="userSpaceOnUse">
      <stop stop-color="#fff" stop-opacity=".26"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </radialGradient>
    <radialGradient id="${uid}-bottom-light" cx="0" cy="0" r="1" gradientTransform="translate(30 65) rotate(-87) scale(36 49)" gradientUnits="userSpaceOnUse">
      <stop stop-color="${lowerGlow}" stop-opacity=".46"/>
      <stop offset="1" stop-color="${to}" stop-opacity="0"/>
    </radialGradient>
    <linearGradient id="${uid}-edge" x1="11" y1="5" x2="55" y2="60" gradientUnits="userSpaceOnUse">
      <stop stop-color="#fff" stop-opacity=".74"/>
      <stop offset=".28" stop-color="#fff" stop-opacity=".12"/>
      <stop offset=".72" stop-color="${from}" stop-opacity=".2"/>
      <stop offset="1" stop-color="#EAF2FF" stop-opacity=".62"/>
    </linearGradient>
    <linearGradient id="${uid}-glyph" x1="25" y1="15" x2="38" y2="50" gradientUnits="userSpaceOnUse">
      <stop stop-color="#fff"/>
      <stop offset=".42" stop-color="#F9FBFF"/>
      <stop offset=".76" stop-color="${glyphMid}"/>
      <stop offset="1" stop-color="${glyphBottom}"/>
    </linearGradient>
    <linearGradient id="${uid}-glyph-gloss" x1="26" y1="15" x2="34" y2="42" gradientUnits="userSpaceOnUse">
      <stop stop-color="#fff" stop-opacity=".95"/>
      <stop offset=".48" stop-color="#fff" stop-opacity=".32"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </linearGradient>
    <radialGradient id="${uid}-halo" cx="0" cy="0" r="1" gradientTransform="translate(31 31) scale(25)" gradientUnits="userSpaceOnUse">
      <stop stop-color="#fff" stop-opacity=".19"/>
      <stop offset="1" stop-color="#fff" stop-opacity="0"/>
    </radialGradient>
    <filter id="${uid}-tile-shadow" x="-16%" y="-14%" width="132%" height="140%" color-interpolation-filters="sRGB">
      <feDropShadow dx="0" dy="1.4" stdDeviation="1.4" flood-color="${materialShade}" flood-opacity=".42"/>
      <feDropShadow dx="-.35" dy="-.45" stdDeviation=".38" flood-color="#fff" flood-opacity=".4"/>
    </filter>
    <filter id="${uid}-material" x="-28%" y="-28%" width="156%" height="165%" color-interpolation-filters="sRGB">
      <feDropShadow dx="0" dy="1.4" stdDeviation=".88" flood-color="${materialShade}" flood-opacity=".64"/>
      <feDropShadow dx="-.55" dy="-.7" stdDeviation=".48" flood-color="#fff" flood-opacity=".95"/>
      <feDropShadow dx=".3" dy=".45" stdDeviation=".34" flood-color="#B7CBF5" flood-opacity=".7"/>
    </filter>
    <clipPath id="${uid}-clip"><path d="${squircle}"/></clipPath>
  </defs>
  <g filter="url(#${uid}-tile-shadow)">
    <path d="${squircle}" fill="url(#${uid}-bg)"/>
    <path d="${squircle}" fill="url(#${uid}-top-light)"/>
    <path d="${squircle}" fill="url(#${uid}-bottom-light)"/>
    <path d="${squircle}" fill="none" stroke="url(#${uid}-edge)" stroke-width="1.45"/>
    <path d="M8 42c10 9 37 11 50-2v8c-2 9-7 14-18 15H21C10 62 4 55 2 46l6-4Z" fill="#D7E5FF" opacity=".1" clip-path="url(#${uid}-clip)"/>
  </g>
  <circle cx="32" cy="32" r="25" fill="url(#${uid}-halo)"/>
  <g filter="url(#${uid}-material)">${body}</g>
  <g opacity=".66" transform="translate(-.35 -.52)">${gloss}</g>
</svg>
`
}

const buildLoaderSvg = ([slug, title], index) => {
  const uid = `${slug}-${index + 1}-loader`
  return `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64" role="img" aria-labelledby="${uid}-title">
  <title id="${uid}-title">${title} loader mark</title>
  ${abstractSymbol(index)}
</svg>
`
}

await mkdir(outputDir, { recursive: true })
await mkdir(loaderDir, { recursive: true })

const manifest = logos.map(([slug, title], index) => {
  const file = `${String(index + 1).padStart(2, "0")}-${slug}.svg`
  return { id: index + 1, slug, title, file: `/service-logos/${file}`, loaderFile: `/service-logos/loader-marks/${file}`, palette: palettes[index % palettes.length] }
})

await Promise.all(logos.map((logo, index) => writeFile(path.join(outputDir, manifest[index].file.split("/").pop()), buildSvg(logo, index))))
await Promise.all(logos.map((logo, index) => writeFile(path.join(loaderDir, manifest[index].file.split("/").pop()), buildLoaderSvg(logo, index))))
await writeFile(path.join(outputDir, "manifest.json"), `${JSON.stringify(manifest, null, 2)}\n`)

const spriteSymbols = logos.map((logo, index) => {
  const svg = buildSvg(logo, index)
    .replace(/^<svg[^>]*>\n\s*<title[^>]*>.*?<\/title>\n/, "")
    .replace(/<\/svg>\s*$/, "")
  return `  <symbol id="logo-${logo[0]}" viewBox="0 0 64 64">\n${svg}  </symbol>`
}).join("\n")
await writeFile(path.join(outputDir, "sprite.svg"), `<svg xmlns="http://www.w3.org/2000/svg">\n${spriteSymbols}\n</svg>\n`)

const cards = manifest.map(item => `
      <article>
        <img src="${item.file}" alt="${item.title}"/>
        <span><b>${String(item.id).padStart(2, "0")}</b>${item.title}</span>
        <button type="button" data-file="${item.file}">Copy path</button>
      </article>`).join("")

await writeFile(path.join(root, "public", "service-logos-preview.html"), `<!doctype html>
<html lang="ru"><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>Service logos · 50</title><style>
*{box-sizing:border-box}body{margin:0;background:#0d0d0e;color:#f4f4f5;font:14px/1.4 system-ui,sans-serif}main{max-width:1180px;margin:auto;padding:56px 28px 80px}h1{margin:0;font-size:40px;letter-spacing:-.04em}p{margin:8px 0 36px;color:#777}.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(150px,1fr));gap:12px}article{padding:18px;display:grid;gap:14px;border:1px solid #28282b;border-radius:18px;background:#161618}img{width:72px;height:72px;filter:drop-shadow(0 12px 18px #0007)}span{display:flex;gap:8px;align-items:center;font-weight:650}b{color:#666;font-size:11px}button{padding:8px 10px;border:1px solid #303034;border-radius:9px;background:#1f1f22;color:#999;cursor:pointer}button:hover{color:#fff;border-color:#555}
</style></head><body><main><h1>Service logos</h1><p>50 scalable SVG marks · 64×64 viewBox · no external dependencies</p><section class="grid">${cards}</section></main><script>document.addEventListener('click',event=>{const button=event.target.closest('button[data-file]');if(!button)return;navigator.clipboard.writeText(button.dataset.file);button.textContent='Copied';setTimeout(()=>button.textContent='Copy path',900)})</script></body></html>
`)

console.log(`Generated ${logos.length} SVG logos in ${path.relative(root, outputDir)}`)
