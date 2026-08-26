import { createContext as e, forwardRef as t, useCallback as n, useContext as r, useEffect as i, useId as a, useImperativeHandle as o, useLayoutEffect as s, useRef as c, useState as l } from "react";
import { AnimatePresence as u, motion as d, useMotionValue as f, useReducedMotion as p, useSpring as m, useTransform as h } from "motion/react";
//#region \0rolldown/runtime.js
var g = (e, t) => () => (t || (e((t = { exports: {} }).exports, t), e = null), t.exports), _ = /* @__PURE__ */ ((e) => typeof require < "u" ? require : typeof Proxy < "u" ? new Proxy(e, { get: (e, t) => (typeof require < "u" ? require : e)[t] }) : e)(function(e) {
	if (typeof require < "u") return require.apply(this, arguments);
	throw Error("Calling `require` for \"" + e + "\" in an environment that doesn't expose the `require` function. See https://rolldown.rs/in-depth/bundling-cjs#require-external-modules for more details.");
});
//#endregion
//#region src/vendor/thinking-logos/bake/mask.ts
function v(e, t, n) {
	return t < 0 || n < 0 || t >= e.w || n >= e.h ? 0 : e.a[n * e.w + t];
}
function y(e, t, n) {
	let r = Math.floor(t), i = Math.floor(n), a = t - r, o = n - i, s = v(e, r, i), c = v(e, r + 1, i), l = v(e, r, i + 1), u = v(e, r + 1, i + 1);
	return s + (c - s) * a + (l - s) * o + (s - c - l + u) * a * o;
}
function b(e, t) {
	if (typeof document > "u") throw Error("thinking-logos: bake requires a DOM. Bake once in the browser, then ship the serialised point set.");
	let n = document.createElement("canvas");
	n.width = e, n.height = t;
	let r = n.getContext("2d", { willReadFrequently: !0 });
	if (!r) throw Error("thinking-logos: could not acquire a 2D context");
	return {
		ctx: r,
		el: n
	};
}
function x(e, t, n) {
	let r = e.getImageData(0, 0, t, n).data, i = new Float32Array(t * n);
	for (let e = 0; e < i.length; e++) i[e] = r[e * 4 + 3] / 255;
	return {
		w: t,
		h: n,
		a: i
	};
}
function S(e, t, n, r) {
	let i = e.w, a = e.h, o = -1, s = -1;
	for (let t = 0; t < e.h; t++) for (let n = 0; n < e.w; n++) e.a[t * e.w + n] < r || (n < i && (i = n), n > o && (o = n), t < a && (a = t), t > s && (s = t));
	if (o < 0) return {
		w: t,
		h: t,
		a: new Float32Array(t * t)
	};
	let c = o - i + 1, l = s - a + 1, u = t * (1 - 2 * n) / Math.max(c, l), d = c * u, f = l * u, p = (t - d) / 2, m = (t - f) / 2, { ctx: h } = b(t, t), g = b(e.w, e.h), _ = g.ctx.createImageData(e.w, e.h);
	for (let t = 0; t < e.a.length; t++) _.data[t * 4] = 255, _.data[t * 4 + 1] = 255, _.data[t * 4 + 2] = 255, _.data[t * 4 + 3] = Math.round(e.a[t] * 255);
	return g.ctx.putImageData(_, 0, 0), h.imageSmoothingQuality = "high", h.drawImage(g.el, i, a, c, l, p, m, d, f), x(h, t, t);
}
async function C(e, t) {
	let n = new DOMParser().parseFromString(e, "image/svg+xml"), r = n.documentElement;
	if (r.nodeName !== "svg" || n.querySelector("parsererror")) throw Error("thinking-logos: input is not valid SVG markup");
	if (!r.getAttribute("viewBox")) {
		let e = Number.parseFloat(r.getAttribute("width") || "0"), t = Number.parseFloat(r.getAttribute("height") || "0");
		e > 0 && t > 0 && r.setAttribute("viewBox", `0 0 ${e} ${t}`);
	}
	r.setAttribute("width", String(t)), r.setAttribute("height", String(t)), r.setAttribute("preserveAspectRatio", "xMidYMid meet");
	let i = new XMLSerializer().serializeToString(r), a = `data:image/svg+xml;charset=utf-8,${encodeURIComponent(i)}`, o = new Image();
	o.decoding = "sync", await new Promise((e, t) => {
		o.onload = () => e(), o.onerror = () => t(/* @__PURE__ */ Error("thinking-logos: the browser could not render this SVG")), o.src = a;
	});
	let { ctx: s } = b(t, t);
	return s.drawImage(o, 0, 0, t, t), x(s, t, t);
}
function w(e, t, n) {
	let { ctx: r } = b(n, n), i = n / t;
	return r.setTransform(i, 0, 0, i, 0, 0), r.fillStyle = "#fff", r.fill(new Path2D(e)), r.setTransform(1, 0, 0, 1, 0, 0), x(r, n, n);
}
function T(e, t) {
	let { ctx: n } = b(t, t);
	return n.drawImage(e, 0, 0, t, t), x(n, t, t);
}
//#endregion
//#region src/vendor/thinking-logos/bake/contour.ts
var E = {
	1: [["T", "L"]],
	2: [["R", "T"]],
	3: [["R", "L"]],
	4: [["B", "R"]],
	5: [["T", "L"], ["B", "R"]],
	6: [["B", "T"]],
	7: [["B", "L"]],
	8: [["L", "B"]],
	9: [["T", "B"]],
	10: [["R", "T"], ["L", "B"]],
	11: [["R", "B"]],
	12: [["L", "R"]],
	13: [["T", "R"]],
	14: [["L", "T"]]
}, D = {
	5: [["T", "R"], ["B", "L"]],
	10: [["R", "B"], ["L", "T"]]
};
function O(e, t, n) {
	let r = t - e;
	return Math.abs(r) < 1e-9 ? .5 : Math.min(1, Math.max(0, (n - e) / r));
}
function k(e, t, n, r, i, a, o, s) {
	switch (e) {
		case "T": return [t + O(r, i, s), n];
		case "R": return [t + 1, n + O(i, a, s)];
		case "B": return [t + O(o, a, s), n + 1];
		default: return [t, n + O(r, o, s)];
	}
}
function A(e) {
	return `${Math.round(e[0] * 1e3)},${Math.round(e[1] * 1e3)}`;
}
function j(e, t) {
	let n = [];
	for (let r = 0; r < e.h - 1; r++) for (let i = 0; i < e.w - 1; i++) {
		let a = v(e, i, r), o = v(e, i + 1, r), s = v(e, i + 1, r + 1), c = v(e, i, r + 1), l = 0;
		if (a >= t && (l |= 1), o >= t && (l |= 2), s >= t && (l |= 4), c >= t && (l |= 8), l === 0 || l === 15) continue;
		let u = E[l];
		(l === 5 || l === 10) && (a + o + s + c) / 4 >= t && (u = D[l]);
		for (let [e, l] of u) n.push([k(e, i, r, a, o, s, c, t), k(l, i, r, a, o, s, c, t)]);
	}
	let r = /* @__PURE__ */ new Map();
	n.forEach(([e], t) => {
		let n = A(e), i = r.get(n);
		i ? i.push(t) : r.set(n, [t]);
	});
	let i = new Uint8Array(n.length), a = [];
	for (let e = 0; e < n.length; e++) {
		if (i[e]) continue;
		let t = [n[e][0]], o = e;
		i[o] = 1;
		for (let e = 0; e < n.length; e++) {
			let e = n[o][1];
			t.push(e);
			let a = (r.get(A(e)) || []).find((e) => !i[e]);
			if (a === void 0) break;
			i[a] = 1, o = a;
		}
		t.length > 3 && a.push(t);
	}
	return a;
}
function M(e) {
	let t = 0;
	for (let n = 0; n < e.length; n++) {
		let r = e[n], i = e[(n + 1) % e.length];
		t += Math.hypot(i[0] - r[0], i[1] - r[1]);
	}
	return t;
}
function N(e, t) {
	let n = M(e);
	if (n <= 0 || t <= 0) return [];
	let r = [], i = 0, a = 0;
	for (let o = 0; o < t; o++) {
		let s = o / t * n;
		for (; i < e.length - 1;) {
			let t = e[i], n = e[(i + 1) % e.length], r = Math.hypot(n[0] - t[0], n[1] - t[1]);
			if (a + r >= s) break;
			a += r, i++;
		}
		let c = e[i], l = e[(i + 1) % e.length], u = Math.hypot(l[0] - c[0], l[1] - c[1]), d = u > 0 ? Math.min(1, (s - a) / u) : 0;
		r.push([c[0] + (l[0] - c[0]) * d, c[1] + (l[1] - c[1]) * d]);
	}
	return r;
}
function P(e, t, n, r) {
	let i = j(e, t).filter((e) => M(e) >= r);
	if (!i.length) return [];
	let a = i.map(M), o = a.reduce((e, t) => e + t, 0), s = [];
	for (let e = 0; e < i.length; e++) {
		let t = Math.max(3, Math.round(a[e] / o * n));
		s.push(...N(i[e], t));
	}
	return s;
}
//#endregion
//#region src/vendor/thinking-logos/bake/fill.ts
function F(e) {
	let t = e >>> 0;
	return () => {
		t = t + 1831565813 >>> 0;
		let e = Math.imul(t ^ t >>> 15, 1 | t);
		return e = e + Math.imul(e ^ e >>> 7, 61 | e) ^ e, ((e ^ e >>> 14) >>> 0) / 4294967296;
	};
}
function I(e, t, n, r) {
	let i = F(r), a = n / Math.SQRT2, o = Math.ceil(e.w / a), s = Math.ceil(e.h / a), c = new Int32Array(o * s).fill(-1), l = [], u = [], d = (e) => Math.floor(e[1] / a) * o + Math.floor(e[0] / a), f = (r) => {
		if (r[0] < 0 || r[1] < 0 || r[0] >= e.w || r[1] >= e.h || y(e, r[0], r[1]) < t) return !1;
		let i = Math.floor(r[0] / a), u = Math.floor(r[1] / a);
		for (let e = Math.max(0, u - 2); e <= Math.min(s - 1, u + 2); e++) for (let t = Math.max(0, i - 2); t <= Math.min(o - 1, i + 2); t++) {
			let i = c[e * o + t];
			if (i < 0) continue;
			let a = l[i];
			if (Math.hypot(a[0] - r[0], a[1] - r[1]) < n) return !1;
		}
		return !0;
	}, p = (e) => {
		c[d(e)] = l.length, u.push(l.length), l.push(e);
	}, m = Math.max(1, Math.floor(n / 2)), h = 0, g = 0, _ = () => {
		for (; g < e.h; g += m, h = 0) for (; h < e.w; h += m) {
			let e = [h + .5, g + .5];
			if (f(e)) return e;
		}
		return null;
	};
	for (;;) {
		let e = _();
		if (!e) break;
		for (p(e); u.length;) {
			let e = Math.floor(i() * u.length), t = l[u[e]], r = !1;
			for (let e = 0; e < 24; e++) {
				let e = i() * Math.PI * 2, a = n * (1 + i()), o = [t[0] + Math.cos(e) * a, t[1] + Math.sin(e) * a];
				if (f(o)) {
					p(o), r = !0;
					break;
				}
			}
			r || u.splice(e, 1);
		}
	}
	return l;
}
function L(e, t, n, r) {
	let i = 0;
	for (let n = 0; n < e.a.length; n++) e.a[n] >= t && i++;
	if (!i) return [];
	let a = Math.max(.5, Math.sqrt(i / n) * 1.07), o = a / 2, s = a * 2, c = I(e, t, a, r);
	for (let i = 0; i < 7 && !(Math.abs(c.length - n) <= Math.max(2, n * .04)); i++) {
		let i = (o + s) / 2, a = I(e, t, i, r);
		a.length > n ? o = i : s = i, Math.abs(a.length - n) < Math.abs(c.length - n) && (c = a);
	}
	return c;
}
//#endregion
//#region src/vendor/thinking-logos/bake/shell.ts
function R(e, t) {
	let { w: n, h: r } = e, i = new Float32Array(n * r);
	for (let n = 0; n < i.length; n++) i[n] = e.a[n] >= t ? 1e9 : 0;
	let a = (e, t) => e < 0 || t < 0 || e >= n || t >= r ? 0 : i[t * n + e];
	for (let e = 0; e < r; e++) for (let t = 0; t < n; t++) {
		let r = e * n + t;
		i[r] !== 0 && (i[r] = Math.min(i[r], a(t - 1, e) + 3, a(t, e - 1) + 3, a(t - 1, e - 1) + 4, a(t + 1, e - 1) + 4));
	}
	for (let e = r - 1; e >= 0; e--) for (let t = n - 1; t >= 0; t--) {
		let r = e * n + t;
		i[r] !== 0 && (i[r] = Math.min(i[r], a(t + 1, e) + 3, a(t, e + 1) + 3, a(t + 1, e + 1) + 4, a(t - 1, e + 1) + 4));
	}
	for (let e = 0; e < i.length; e++) i[e] /= 3;
	return i;
}
function z(e, t, n, r, i) {
	let a = Math.min(t - 1, Math.max(0, Math.round(r)));
	return e[Math.min(n - 1, Math.max(0, Math.round(i))) * t + a];
}
function B(e, t, n, r, i, a) {
	let o = R(n, r), s = 1e-6;
	for (let e = 0; e < o.length; e++) o[e] > s && (s = o[e]);
	let c = n.w / 2, l = (e) => (e - c) / c, u = (e) => -(e - n.h / 2) / (n.h / 2), d = (e) => Math.min(1, z(o, n.w, n.h, e[0], e[1]) / s), f = [];
	if (i === "flat") {
		for (let t of e) f.push({
			x: l(t[0]),
			y: u(t[1]),
			z: 0,
			e: d(t)
		});
		return f;
	}
	if (i === "dome") {
		for (let t of e) {
			let e = d(t);
			f.push({
				x: l(t[0]),
				y: u(t[1]),
				z: a * Math.sqrt(e),
				e
			});
		}
		return f;
	}
	let p = a / 2;
	for (let t of e) {
		let e = d(t);
		f.push({
			x: l(t[0]),
			y: u(t[1]),
			z: p,
			e
		}), f.push({
			x: l(t[0]),
			y: u(t[1]),
			z: -p,
			e
		});
	}
	let m = Math.max(1, Math.round(a * 6));
	for (let e = 1; e <= m; e++) {
		let n = p - e / (m + 1) * a;
		for (let e of t) f.push({
			x: l(e[0]),
			y: u(e[1]),
			z: n,
			e: 0
		});
	}
	return f;
}
//#endregion
//#region src/vendor/thinking-logos/bake/bake.ts
var V = {
	count: 260,
	style: "fill",
	shell: "dome",
	depth: .34,
	resolution: 256,
	threshold: .5,
	margin: .06,
	seed: 1
};
function ee(e, t) {
	let n = Math.round(e * e / 5.5), r = t === "outline" ? Math.round(e * 2.6) : n;
	return Math.max(24, Math.min(900, r));
}
async function te(e, t) {
	return "mask" in e ? e.mask : "svg" in e ? C(e.svg, t) : "path" in e ? w(e.path, e.viewBox ?? 24, t) : T(e.image, t);
}
async function ne(e, t = {}) {
	let n = {
		...V,
		...t
	}, r = S(await te(e, n.resolution), n.resolution, n.margin, n.threshold), i = n.style !== "fill" || n.shell === "slab", a = n.style === "both" ? Math.round(n.count * .42) : n.count, o = Math.max(6, n.resolution / Math.sqrt(n.count) * 3), s = i ? P(r, n.threshold, a, o) : [], c;
	c = n.style === "outline" ? s : n.style === "fill" ? L(r, n.threshold, n.count, n.seed) : [...s, ...L(r, n.threshold, n.count - s.length, n.seed)];
	let l = B(c, s, r, n.threshold, n.shell, n.depth), u = l.length, d = new Float32Array(u * 3), f = new Float32Array(u);
	for (let e = 0; e < u; e++) d[e * 3] = l[e].x, d[e * 3 + 1] = l[e].y, d[e * 3 + 2] = l[e].z, f[e] = l[e].e;
	return {
		version: 1,
		n: u,
		p: d,
		e: f,
		style: n.style,
		shell: n.shell
	};
}
//#endregion
//#region src/vendor/thinking-logos/engine/core.ts
function re(e, t) {
	let n = Math.floor(e), r = Math.floor(t), i = e - n, a = t - r;
	i = i * i * (3 - 2 * i), a = a * a * (3 - 2 * a);
	let o = H(n, r), s = H(n + 1, r), c = H(n, r + 1), l = H(n + 1, r + 1);
	return o + (s - o) * i + (c - o) * a + (o - s - c + l) * i * a;
}
function H(e, t) {
	let n = Math.sin(e * 12.9898 + t * 78.233) * 43758.5453;
	return n - Math.floor(n);
}
function ie(e, t) {
	let n = Math.PI * (3 - Math.sqrt(5)), r = 1 - 2 * (e + .5) / t, i = Math.sqrt(1 - r * r), a = e * n;
	return [
		i * Math.cos(a),
		r,
		i * Math.sin(a)
	];
}
function ae(e, t) {
	return Math.atan2(Math.sin(e - t), Math.cos(e - t));
}
function U(e, t, n, r, i) {
	let a = Math.sin(t), o = Math.cos(t), s = Math.sin(e), c = Math.cos(e);
	return (e, t, l) => {
		let u = e * c + l * s, d = -e * s + l * c, f = t * o - d * a, p = t * a + d * o;
		return [
			n + u * i,
			r - f * i,
			p
		];
	};
}
function oe(e, t, n, r = .3) {
	for (let r of t) {
		let t = r.a ?? 1, i = Math.min(1, Math.max(0, r.white)), a = Math.round((n ? 1 - i : i) * 255);
		e.fillStyle = `rgba(${a},${a},${a},${t})`, e.beginPath(), e.arc(r.x, r.y, r.r, 0, Math.PI * 2), e.fill();
	}
}
function se(e, t, n) {
	for (let r of t) {
		let t = r.a ?? 1, i = Math.min(1, Math.max(0, r.white)), a = Math.round((n ? 1 - i : i) * 255);
		e.strokeStyle = `rgba(${a},${a},${a},${t})`, e.lineWidth = r.w, e.beginPath(), e.moveTo(r.x1, r.y1), e.lineTo(r.x2, r.y2), e.stroke();
	}
}
function W(e, t, n = .3) {
	let r = [];
	for (let t of e) (t.a ?? 1) < .02 || (t.r = Math.max(n, t.r), r.push(t));
	return r.sort((e, t) => e.z - t.z), {
		dots: r,
		lines: t.filter((e) => (e.a ?? 1) >= .02)
	};
}
function ce(e, t, n) {
	t.lines.length && se(e, t.lines, n), oe(e, t.dots, n);
}
function G(e, t) {
	return (e / 300) ** t;
}
//#endregion
//#region src/vendor/thinking-logos/engine/tint.ts
function le(e) {
	let t = e.trim(), n = t.startsWith("#") ? t.slice(1) : null;
	if (n && (n.length === 3 || n.length === 6)) {
		let e = n.length === 3 ? n.replace(/./g, (e) => e + e) : n, t = Number.parseInt(e, 16);
		return Number.isNaN(t) ? null : {
			r: t >> 16 & 255,
			g: t >> 8 & 255,
			b: t & 255
		};
	}
	let r = t.split(",").map((e) => Number.parseInt(e, 10));
	return r.length === 3 && r.every((e) => Number.isFinite(e)) ? {
		r: r[0],
		g: r[1],
		b: r[2]
	} : null;
}
function ue(e) {
	return (.2126 * e.r + .7152 * e.g + .0722 * e.b) / 255;
}
function de(e, t) {
	let n = ue(e);
	if (t && n < .42) {
		let t = (.42 - n) / (1 - n);
		return {
			r: Math.round(e.r + (255 - e.r) * t),
			g: Math.round(e.g + (255 - e.g) * t),
			b: Math.round(e.b + (255 - e.b) * t)
		};
	}
	if (!t && n > .62) {
		let t = (n - .62) / n;
		return {
			r: Math.round(e.r * (1 - t)),
			g: Math.round(e.g * (1 - t)),
			b: Math.round(e.b * (1 - t))
		};
	}
	return e;
}
function fe(e, t, n, r = 1) {
	let i = 255 * t, a = (e) => {
		let a = n ? e * t : 255 + (e - 255) * (1 - t), o = n ? i : 255 - (255 - i);
		return Math.round(o + (a - o) * r);
	};
	return `${a(e.r)},${a(e.g)},${a(e.b)}`;
}
function pe(e, t, n, r) {
	for (let i of t.lines) {
		let t = Math.min(1, Math.max(0, i.white));
		e.strokeStyle = `rgba(${fe(r, n ? 1 - t : t, n)},${i.a ?? 1})`, e.lineWidth = i.w, e.beginPath(), e.moveTo(i.x1, i.y1), e.lineTo(i.x2, i.y2), e.stroke();
	}
	for (let i of t.dots) {
		let t = Math.min(1, Math.max(0, i.white));
		e.fillStyle = `rgba(${fe(r, n ? 1 - t : t, n, i.k ?? 1)},${i.a ?? 1})`, e.beginPath(), e.arc(i.x, i.y, i.r, 0, Math.PI * 2), e.fill();
	}
}
//#endregion
//#region src/vendor/thinking-logos/engine/logo.ts
var me = Math.PI * 2;
function he(e) {
	return e * e * (3 - 2 * e);
}
function ge(e) {
	return e < 0 ? 0 : e > 1 ? 1 : e;
}
function _e(e) {
	let t = e.n, n = new Uint32Array(t), r = new Uint32Array(t), i = new Float32Array(t), a = new Float32Array(t);
	for (let o = 0; o < t; o++) {
		n[o] = o, r[o] = o, i[o] = Math.atan2(e.p[o * 3 + 1], e.p[o * 3]);
		let [s, c] = ie(o, t);
		a[o] = Math.atan2(c, s);
	}
	n.sort((e, t) => i[e] - i[t]), r.sort((e, t) => a[e] - a[t]);
	let o = new Uint32Array(t);
	for (let e = 0; e < t; e++) o[n[e]] = r[e];
	return o;
}
function ve() {
	return {
		dots: [],
		lines: []
	};
}
function K(e, t, n) {
	let r = e.inkFar ?? .6, i = e.inkSpan ?? .5, a = e.inkRim ?? .16;
	return r - i * t - a * (1 - n);
}
var ye = (e, t, n, r) => {
	if (!r) return ve();
	let { p: i, e: a, n: o } = r.points, s = r.seats, c = e / 2, l = e / 2 * .82, u = G(e, n.rsPow ?? .6), d = q(t, n.dwell ?? 5.5, n.morph ?? 1.9, n.turns ?? 1, n.settle ?? .1, n.expo ?? .3), f = d.m, p = 1 - f, m = me * d.turns, h = U(m, (n.tiltAmp ?? .34) * p, c, c, l), g = n.sphereR ?? .94, _ = n.scanWidth ?? .22, v = m + Math.PI / 2 + (n.scanSwing ?? 1.05) * Math.sin(t * (n.scanRate ?? .85)), y = n.dimBase ?? .4, b = n.poleEase ?? 1.4, x = Math.max(3, Math.round(n.arms ?? 13)), S = n.armDepth ?? .55, C = [];
	for (let e = 0; e < o; e++) {
		let [t, r, c] = ie(s[e], o), l = (r < 0 ? -1 : 1) * Math.abs(r) ** b, d = Math.sqrt(Math.max(1e-9, 1 - r * r)), m = Math.sqrt(Math.max(0, 1 - l * l)) / d, w = t * m, T = l, E = c * m, D = s[e] % x % 3, O = 1 - S * (D === 0 ? 0 : D === 1 ? .5 : 1), k = w * g, A = T * g, j = E * g, M = i[e * 3] + (k - i[e * 3]) * p, N = i[e * 3 + 1] + (A - i[e * 3 + 1]) * p, P = i[e * 3 + 2] + (j - i[e * 3 + 2]) * p, F = ae(Math.atan2(E, w), v), I = Math.exp(-(F * F) / _) * p, [L, R, z] = h(M, N, P), B = ge((z + 1) / 2);
		C.push({
			x: L,
			y: R,
			z,
			r: ((n.rBase ?? .5) + (n.rDepth ?? 1.4) * B * O + (n.rBoost ?? 1.3) * I) * u,
			white: K(n, B, a[e] * f + (1 - f)) + (n.armInk ?? .16) * (1 - O) * p - (n.scanInk ?? .3) * I,
			a: 1 - (1 - y) * p * (1 - Math.min(1, I))
		});
	}
	return W(C, [], n.rMin);
};
function be(e) {
	return e <= 0 ? 0 : e >= 1 ? 1 : e < .5 ? 2 ** (20 * e - 10) / 2 : (2 - 2 ** (-20 * e + 10)) / 2;
}
function xe(e, t) {
	let n = e * e * e * (e * (e * 6 - 15) + 10);
	return n + (be(e) - n) * t;
}
function Se(e, t) {
	let n = Math.min(.49, Math.max(.001, t)), r = 1 / (1 - n);
	if (e <= 0) return 0;
	if (e >= 1) return 1;
	if (e < n) {
		let t = e / n;
		return r * n * (t * t * t - t * t * t * t / 2);
	}
	if (e > 1 - n) {
		let t = (1 - e) / n;
		return 1 - r * n * (t * t * t - t * t * t * t / 2);
	}
	return r * (n * .5 + (e - n));
}
function q(e, t, n, r, i, a = .3) {
	let o = t + n * 2, s = e % o, c = t + n * i, l = r * Se(Math.min(1, s / c), .22);
	if (s < t) return {
		m: 0,
		turns: l,
		workT: s,
		local: s,
		cycle: o
	};
	let u = s - t;
	return u < n ? {
		m: xe(u / n, a),
		turns: l,
		workT: -1,
		local: s,
		cycle: o
	} : {
		m: xe(1 - (u - n) / n, a),
		turns: l,
		workT: -1,
		local: s,
		cycle: o
	};
}
function Ce(e, t, n) {
	return he(ge(t * (1 + n) - H(e, 3.1) * n));
}
var we = (e, t, n, r) => {
	if (!r) return ve();
	let { p: i, e: a, n: o } = r.points, s = r.seats, c = e / 2, l = e / 2 * .82, u = G(e, n.rsPow ?? .6), d = q(t, n.dwell ?? 5.5, n.morph ?? 1.9, n.turns ?? 1, n.settle ?? .45, n.expo ?? .3), f = d.m, p = U(me * d.turns, (n.tiltAmp ?? .34) * (1 - f), c, c, l), m = n.stagger ?? 0, h = n.arc ?? 0, g = n.churn ?? .09, _ = n.sphereR ?? .92, v = n.haloShare ?? .12, y = [];
	for (let e = 0; e < o; e++) {
		let r = m > 0 ? Ce(e, f, m) : f, c = s[e], [l, d, b] = ie(c, o), x = _ * (1 + g * (re(l * 2 + t * .7, b * 2) - .5) * 2), S = i[e * 3], C = i[e * 3 + 1], w = i[e * 3 + 2], T = 0;
		if (H(e, 6.7) < v) {
			T = f;
			let r = Math.sin(t * (n.haloRate ?? .9) + H(e, 8.3) * me), i = 1 + (n.haloOut ?? .18) * (.5 + .5 * r) * T;
			S *= i, C *= i, w += (n.haloZ ?? .8) * r * T;
		}
		let E = l * x + (S - l * x) * r, D = d * x + (C - d * x) * r, O = b * x + (w - b * x) * r;
		if (h > 0) {
			let e = 1 + h * Math.sin(Math.PI * r);
			E *= e, D *= e, O *= e;
		}
		let [k, A, j] = p(E, D, O), M = ge((j + 1) / 2), N = Math.sin(Math.PI * r);
		y.push({
			x: k,
			y: A,
			z: j,
			r: ((n.rBase ?? .55) + (n.rDepth ?? 1.5) * M + (n.haloR ?? .22) * T) * u,
			white: K(n, M, a[e] * r + (1 - r)),
			a: 1 - (n.flightFade ?? .25) * N
		});
	}
	return W(y, [], n.rMin);
}, Te = (e, t, n, r) => {
	if (!r) return ve();
	let { p: i, e: a, n: o } = r.points, s = r.seats, c = e / 2, l = e / 2 * .82, u = G(e, n.rsPow ?? .6), d = n.dwell ?? 5.5, f = n.morph ?? 1.9, p = q(t, d, f, n.turns ?? 0, n.settle ?? .1, n.expo ?? .3), m = p.m, h = 1 - m, g = U((n.lean ?? .4) + (n.yawAmp ?? .3) * Math.sin(t * (n.yawRate ?? .26)) * h, (n.tilt ?? .4) * h, c, c, l), _ = p.local - d, v = (p.local < d ? p.local / d : _ < f ? 1 : ge(1 - (_ - f) / f)) * o, y = Math.max(1, o * (n.feather ?? .02)), b = Math.max(1, o * (n.headWidth ?? .01)), x = p.local < d, S = n.wraps ?? 3, C = n.knotTurns ?? 2, w = n.major ?? .62, T = n.minor ?? .3, E = t * (n.spin ?? .24), D = [];
	for (let e = 0; e < o; e++) {
		let t = s[e], r = t / o * me, c = w + T * Math.cos(C * r), l = c * Math.cos(S * r), d = T * Math.sin(C * r), f = c * Math.sin(S * r), p = Math.cos(E), _ = Math.sin(E), O = l * p + f * _, k = -l * _ + f * p, A = i[e * 3], j = i[e * 3 + 1], M = i[e * 3 + 2], N = A + (O - A) * h, P = j + (d - j) * h, F = M + (k - M) * h, I = ge((v - t) / y), L = x ? Math.exp(-(((t - v) / b) ** 2)) : 0, [R, z, B] = g(N, P, F), V = ge((B + 1) / 2);
		D.push({
			x: R,
			y: z,
			z: B,
			r: ((n.rBase ?? .55) + (n.rDepth ?? 1.4) * V + (n.headR ?? 1.2) * L * h) * u,
			white: K(n, V, a[e] * m + (1 - m)) - (n.headInk ?? .4) * L * h,
			a: 1 - (1 - I) * h
		});
	}
	return W(D, [], n.rMin);
};
//#endregion
//#region src/vendor/thinking-logos/engine/lattice.ts
function Ee(e, t, n, r) {
	let i = e % (2 * t * n + r), a = Array(t).fill(0), o = -1;
	if (i < 2 * t * n) {
		let e = Math.floor(i / n), r = (i - e * n) / n, s = 1 - (1 - Math.min(1, r / .7)) ** 3;
		if (e < t) {
			for (let t = 0; t < e; t++) a[t] = 1;
			a[e] = s, o = e;
		} else {
			let n = 2 * t - 1 - e;
			for (let e = 0; e < n; e++) a[e] = 1;
			a[n] = 1 - s, o = n;
		}
	}
	return {
		amount: a,
		active: o
	};
}
function De(e, t, n) {
	let [r, i, a] = e, o = !1;
	for (let e = 0; e < t.length; e++) {
		if (n.amount[e] <= 0) continue;
		let s = t[e], c = s.axis === 0 ? r : s.axis === 1 ? i : a;
		if (c < s.lo || c >= s.hi) continue;
		e === n.active && (o = !0);
		let l = s.ang * n.amount[e], u = Math.cos(l), d = Math.sin(l);
		if (s.axis === 0) {
			let e = i * u - a * d;
			a = i * d + a * u, i = e;
		} else if (s.axis === 1) {
			let e = r * u + a * d;
			a = -r * d + a * u, r = e;
		} else {
			let e = r * u - i * d;
			i = r * d + i * u, r = e;
		}
	}
	return [
		r,
		i,
		a,
		o
	];
}
//#endregion
//#region src/vendor/thinking-logos/engine/logoDeform.ts
function J(e) {
	return e < 0 ? 0 : e > 1 ? 1 : e;
}
function Oe() {
	return {
		dots: [],
		lines: []
	};
}
function ke(e, t, n) {
	let [r, i, a] = ie(e, t), o = Math.max(Math.abs(r), Math.abs(i), Math.abs(a)) || 1;
	return [
		r / o * n,
		i / o * n,
		a / o * n
	];
}
function Ae(e, t) {
	let n = [], r = 2 * t / 3;
	for (let i = 0; i < e; i++) {
		let e = Math.min(2, Math.floor(H(i, 2.3) * 3)), a = -t + r * Math.min(2, Math.floor(H(i, 5.9) * 3)), o = H(i, 7.7) < .5 ? 1 : -1;
		n.push({
			axis: e,
			lo: a,
			hi: a + r,
			ang: o * Math.PI / 2
		});
	}
	return n;
}
var je = (e, t, n, r) => {
	if (!r) return Oe();
	let { p: i, e: a, n: o } = r.points, s = r.seats, c = e / 2, l = e / 2 * .82, u = G(e, n.rsPow ?? .6), d = n.cubeHalf ?? .62, f = n.dwell ?? 5.5, p = q(t, f, n.morph ?? 1.9, n.turns ?? 1, n.settle ?? .45, n.expo ?? .3), m = p.m, h = 1 - m, g = U(Math.PI * 2 * p.turns, (n.tiltAmp ?? .36) * h, c, c, l), _ = n.moveCount ?? 6, v = Ee(J(p.workT < 0 ? 1 : p.workT / f) * 2 * _, _, 1, 0), y = Ae(_, d), b = [];
	for (let e = 0; e < o; e++) {
		let [t, r, c] = ke(s[e], o, d), [l, f, p, _] = De([
			t,
			r,
			c
		], y, v), x = i[e * 3], S = i[e * 3 + 1], C = i[e * 3 + 2], [w, T, E] = g(x + (l - x) * h, S + (f - S) * h, C + (p - C) * h), D = J((E + 1) / 2);
		b.push({
			x: w,
			y: T,
			z: E,
			r: ((n.rBase ?? .55) + (n.rDepth ?? 1.4) * D + (_ ? n.rActive ?? .3 : 0) * h) * u,
			white: K(n, D, a[e] * m + (1 - m))
		});
	}
	return W(b, [], n.rMin);
}, Me = (e, t, n, r) => {
	if (!r) return Oe();
	let { p: i, e: a, n: o } = r.points, s = r.seats, c = e / 2, l = e / 2 * .82, u = G(e, n.rsPow ?? .6), d = q(t, n.dwell ?? 5.5, n.morph ?? 1.9, 0, n.settle ?? .45, n.expo ?? .3).m, f = 1 - d, p = U((n.yawAmp ?? .42) * Math.sin(t * (n.yawRate ?? .55)) * f, (n.tiltAmp ?? .26) * f, c, c, l), m = n.wide ?? 1.12, h = n.tall ?? .5, g = n.waveK ?? 3.1, _ = n.waveK2 ?? 6.7, v = n.waveRate ?? 1.9, y = n.swing ?? .52, b = [];
	for (let e = 0; e < o; e++) {
		let [r, c, l] = ie(s[e], o), x = Math.sin(r * g - t * v) * .62 + Math.sin(r * _ + t * v * .55) * .38, S = 1 + y * x, C = 1 + (n.lumps ?? .12) * (re(r * 2 + t * .35, l * 2) - .5) * 2, w = r * m * C, T = c * h * C * S, E = l * m * C, D = i[e * 3], O = i[e * 3 + 1], k = i[e * 3 + 2], [A, j, M] = p(D + (w - D) * f, O + (T - O) * f, k + (E - k) * f), N = J((M + 1) / 2), P = J(x * .5 + .5);
		b.push({
			x: A,
			y: j,
			z: M,
			r: ((n.rBase ?? .55) + (n.rDepth ?? 1.5) * N + (n.loudR ?? .3) * P * f) * u,
			white: K(n, N, a[e] * d + (1 - d)) - (n.loudInk ?? .14) * P * f
		});
	}
	return W(b, [], n.rMin);
}, Ne = (e, t, n, r) => {
	if (!r) return Oe();
	let { p: i, e: a, n: o } = r.points, s = r.seats, c = e / 2, l = e / 2 * .82, u = G(e, n.rsPow ?? .6), d = q(t, n.dwell ?? 5.5, n.morph ?? 1.9, n.turns ?? 0, n.settle ?? .1, n.expo ?? .3).m, f = 1 - d, p = U((n.yawAmp ?? .22) * Math.sin(t * (n.yawRate ?? .3)) * f, (n.tilt ?? .42) * f, c, c, l), m = Math.max(3, Math.round(n.rings ?? 9)), h = Math.ceil(o / m), g = Math.sin(t * (n.breatheRate ?? .75)), _ = n.breatheAmp ?? .2, v = (n.height ?? 1.5) * (1 + _ * g), y = (n.wide ?? .82) * (1 - _ * .72 * g), b = t * (n.spin ?? .16), x = [];
	for (let e = 0; e < o; e++) {
		let t = s[e], r = t % m, o = m > 1 ? r / (m - 1) - .5 : 0, c = Math.cos(o * Math.PI * (n.taper ?? .78)), l = y * c, g = Math.floor(t / m) / h * Math.PI * 2 + b, _ = Math.cos(g) * l, S = o * v, C = Math.sin(g) * l, w = i[e * 3], T = i[e * 3 + 1], E = i[e * 3 + 2], [D, O, k] = p(w + (_ - w) * f, T + (S - T) * f, E + (C - E) * f), A = J((k + 1) / 2), j = J(c);
		x.push({
			x: D,
			y: O,
			z: k,
			r: ((n.rBase ?? .55) + (n.rDepth ?? 1.4) * A + (n.loudR ?? .25) * j * f) * u,
			white: K(n, A, a[e] * d + (1 - d)) - (n.loudInk ?? .12) * j * f
		});
	}
	return W(x, [], n.rMin);
}, Pe = (e, t, n, r) => {
	if (!r) return Oe();
	let { p: i, e: a, n: o } = r.points, s = r.seats, c = e / 2, l = e / 2 * .82, u = G(e, n.rsPow ?? .6), d = n.dwell ?? 5.5, f = n.morph ?? 1.9, p = q(t, d, f, n.turns ?? 0, n.settle ?? .1, n.expo ?? .3), m = p.m, h = 1 - m, g = U((n.lean ?? .5) + (n.yawAmp ?? .24) * Math.sin(t * (n.yawRate ?? .32)) * h, (n.tilt ?? .2) * h, c, c, l), _ = n.crystalR ?? .94, v = t * (n.spin ?? .3), y = p.local - d, b = (p.local < d ? p.local / d : y < f ? 1 : J(1 - (y - f) / f)) * o, x = Math.max(1, o * (n.feather ?? .03)), S = Math.max(1, o * (n.headWidth ?? .012)), C = p.local < d, w = [];
	for (let e = 0; e < o; e++) {
		let t = s[e], [r, c, l] = ie(t, o), d = Math.max(1e-6, Math.abs(r) + Math.abs(c) + Math.abs(l)), f = Math.cos(v), p = Math.sin(v), y = r / d * _, T = c / d * _, E = l / d * _, D = y * f + E * p, O = -y * p + E * f, k = i[e * 3], A = i[e * 3 + 1], j = i[e * 3 + 2], M = k + (D - k) * h, N = A + (T - A) * h, P = j + (O - j) * h, F = J((b - t) / x), I = C ? Math.exp(-(((t - b) / S) ** 2)) : 0, [L, R, z] = g(M, N, P), B = J((z + 1) / 2), V = (1 - F) * h;
		w.push({
			x: L,
			y: R,
			z,
			r: ((n.rBase ?? .55) + (n.rDepth ?? 1.4) * B + (n.headR ?? 1.1) * I * h) * u,
			white: K(n, B, a[e] * m + (1 - m)) + (n.unlitInk ?? .3) * V - (n.headInk ?? .4) * I * h,
			k: 1 - V
		});
	}
	return W(w, [], n.rMin);
}, Fe = {
	thinking: "assemble",
	searching: "scan",
	working: "work",
	solving: "solve",
	listening: "wave",
	waiting: "wait",
	generating: "crystal"
}, Ie = {
	assemble: we,
	scan: ye,
	work: Te,
	solve: je,
	wave: Me,
	wait: Ne,
	crystal: Pe
}, Le = {
	assemble: {
		speed: 1,
		opts: {
			dwell: 5.5,
			turns: 1,
			morph: 1.9,
			expo: .3,
			settle: .1,
			tiltAmp: .34,
			stagger: 0,
			arc: 0,
			churn: .09,
			sphereR: .92,
			flightFade: .25,
			haloShare: .12,
			haloOut: .18,
			haloZ: .8,
			haloRate: .9,
			haloR: .22,
			rBase: .55,
			rDepth: 1.5,
			inkFar: .6,
			inkSpan: .5,
			inkRim: .16,
			rsPow: .6,
			rMin: .3
		}
	},
	scan: {
		speed: 1,
		opts: {
			dwell: 5.5,
			turns: 1,
			morph: 1.9,
			expo: .3,
			settle: .1,
			tiltAmp: .34,
			sphereR: .94,
			poleEase: 1.4,
			arms: 13,
			armDepth: .72,
			armInk: .24,
			scanRate: .85,
			scanSwing: 1.05,
			scanWidth: .22,
			dimBase: .4,
			rBoost: 1.3,
			scanInk: .3,
			rBase: .5,
			rDepth: 1.4,
			inkFar: .6,
			inkSpan: .5,
			inkRim: .16,
			rsPow: .6,
			rMin: .3
		}
	},
	work: {
		speed: 1,
		opts: {
			dwell: 5.5,
			morph: 1.9,
			expo: .3,
			settle: .1,
			turns: 0,
			lean: .4,
			yawAmp: .3,
			yawRate: .26,
			tilt: .4,
			wraps: 3,
			knotTurns: 2,
			major: .62,
			minor: .3,
			spin: .24,
			feather: .02,
			headWidth: .01,
			headR: 1.2,
			headInk: .4,
			rBase: .75,
			rDepth: 1.6,
			inkFar: .6,
			inkSpan: .5,
			inkRim: .16,
			rsPow: .6,
			rMin: .3
		}
	},
	solve: {
		speed: 1,
		opts: {
			dwell: 5.5,
			turns: 1,
			morph: 1.9,
			expo: .3,
			settle: .1,
			tiltAmp: .36,
			cubeHalf: .62,
			moveCount: 6,
			rActive: .3,
			rBase: .55,
			rDepth: 1.4,
			inkFar: .6,
			inkSpan: .5,
			inkRim: .16,
			rsPow: .6,
			rMin: .3
		}
	},
	wave: {
		speed: 1,
		opts: {
			dwell: 5.5,
			morph: 1.9,
			expo: .3,
			settle: .1,
			yawAmp: .42,
			yawRate: .55,
			tiltAmp: .26,
			wide: 1.12,
			tall: .5,
			waveK: 3.1,
			waveK2: 6.7,
			waveRate: 1.9,
			swing: .52,
			lumps: .12,
			loudR: .3,
			loudInk: .14,
			rBase: .55,
			rDepth: 1.5,
			inkFar: .6,
			inkSpan: .5,
			inkRim: .16,
			rsPow: .6,
			rMin: .3
		}
	},
	wait: {
		speed: 1,
		opts: {
			dwell: 5.5,
			morph: 1.9,
			expo: .3,
			settle: .1,
			turns: 0,
			yawAmp: .22,
			yawRate: .3,
			tilt: .42,
			rings: 9,
			height: 1.5,
			wide: .82,
			taper: .78,
			breatheRate: .75,
			breatheAmp: .2,
			spin: .16,
			loudR: .25,
			loudInk: .12,
			rBase: .55,
			rDepth: 1.4,
			inkFar: .6,
			inkSpan: .5,
			inkRim: .16,
			rsPow: .6,
			rMin: .3
		}
	},
	crystal: {
		speed: 1,
		opts: {
			dwell: 5.5,
			morph: 1.9,
			expo: .3,
			settle: .1,
			turns: 0,
			lean: .5,
			yawAmp: .24,
			yawRate: .32,
			tilt: .2,
			crystalR: .94,
			spin: .3,
			feather: .03,
			headWidth: .012,
			headR: 1.1,
			headInk: .4,
			unlitInk: .3,
			rBase: .55,
			rDepth: 1.4,
			inkFar: .6,
			inkSpan: .5,
			inkRim: .16,
			rsPow: .6,
			rMin: .3
		}
	}
};
function Re(e, t, n) {
	let r = Fe[e], i = Le[r], a = {
		...i.opts,
		...n
	};
	return {
		mode: r,
		frame: Ie[r],
		speed: i.speed,
		opts: a,
		binding: {
			points: t,
			seats: _e(t)
		}
	};
}
//#endregion
//#region src/vendor/thinking-logos/theme.ts
function ze(e) {
	let t = e;
	for (; t;) {
		let e = t.getAttribute("data-theme");
		if (e === "dark") return !0;
		if (e === "light") return !1;
		if (t.classList.contains("dark")) return !0;
		if (t.classList.contains("light")) return !1;
		t = t.parentElement;
	}
	return null;
}
function Be() {
	return typeof matchMedia > "u" || matchMedia("(prefers-color-scheme: dark)").matches;
}
function Ve(e, t) {
	let [n, r] = l(!0);
	return i(() => {
		if (e === "dark") {
			r(!0);
			return;
		}
		if (e === "light") {
			r(!1);
			return;
		}
		let n = () => {
			let e = ze(t.current);
			r(e ?? Be());
		};
		n();
		let i = typeof matchMedia < "u" ? matchMedia("(prefers-color-scheme: dark)") : null, a = () => n();
		i?.addEventListener("change", a);
		let o = null;
		return typeof MutationObserver < "u" && t.current && (o = new MutationObserver(n), o.observe(document.documentElement, {
			attributes: !0,
			attributeFilter: ["class", "data-theme"],
			subtree: !0
		})), () => {
			i?.removeEventListener("change", a), o?.disconnect();
		};
	}, [e, t]), n;
}
function He() {
	let [e, t] = l(!1);
	return i(() => {
		if (typeof matchMedia > "u") return;
		let e = matchMedia("(prefers-reduced-motion: reduce)");
		t(e.matches);
		let n = (e) => t(e.matches);
		return e.addEventListener("change", n), () => e.removeEventListener("change", n);
	}, []), e;
}
//#endregion
//#region src/vendor/thinking-logos/useBakedLogo.ts
var Ue = /* @__PURE__ */ new Map();
function We(e, t) {
	let n = "svg" in e ? e.svg : "path" in e ? `p:${e.viewBox ?? 24}:${e.path}` : null;
	if (n === null) return null;
	let r = t;
	return [
		n,
		r.count,
		r.style,
		r.shell,
		r.depth,
		r.resolution,
		r.threshold,
		r.margin,
		r.seed
	].join("\0");
}
function Ge(e, t = {}) {
	let n = We(e, t);
	if (n === null) return ne(e, t);
	let r = Ue.get(n);
	if (r) return r;
	let i = ne(e, t).catch((e) => {
		throw Ue.delete(n), e;
	});
	return Ue.set(n, i), i;
}
function Ke(e, t = {}) {
	let n = "version" in e ? e : null, r = n ? null : We(e, t), [a, o] = l(() => ({
		points: n,
		error: null,
		pending: !n
	})), s = c(e);
	return s.current = e, i(() => {
		if (n) {
			o({
				points: n,
				error: null,
				pending: !1
			});
			return;
		}
		let e = !0;
		return o((e) => ({
			...e,
			pending: !0
		})), Ge(s.current, t).then((t) => {
			e && o({
				points: t,
				error: null,
				pending: !1
			});
		}).catch((t) => {
			e && o({
				points: null,
				error: t,
				pending: !1
			});
		}), () => {
			e = !1;
		};
	}, [r, n]), a;
}
//#endregion
//#region ../node_modules/.pnpm/react@19.2.8/node_modules/react/cjs/react-jsx-runtime.production.js
var qe = /* @__PURE__ */ g(((e) => {
	var t = Symbol.for("react.transitional.element"), n = Symbol.for("react.fragment");
	function r(e, n, r) {
		var i = null;
		if (r !== void 0 && (i = "" + r), n.key !== void 0 && (i = "" + n.key), "key" in n) for (var a in r = {}, n) a !== "key" && (r[a] = n[a]);
		else r = n;
		return n = r.ref, {
			$$typeof: t,
			type: e,
			key: i,
			ref: n === void 0 ? null : n,
			props: r
		};
	}
	e.Fragment = n, e.jsx = r, e.jsxs = r;
})), Je = /* @__PURE__ */ g(((e) => {
	process.env.NODE_ENV !== "production" && (function() {
		function t(e) {
			if (e == null) return null;
			if (typeof e == "function") return e.$$typeof === k ? null : e.displayName || e.name || null;
			if (typeof e == "string") return e;
			switch (e) {
				case v: return "Fragment";
				case b: return "Profiler";
				case y: return "StrictMode";
				case w: return "Suspense";
				case T: return "SuspenseList";
				case O: return "Activity";
			}
			if (typeof e == "object") switch (typeof e.tag == "number" && console.error("Received an unexpected object in getComponentNameFromType(). This is likely a bug in React. Please file an issue."), e.$$typeof) {
				case g: return "Portal";
				case S: return e.displayName || "Context";
				case x: return (e._context.displayName || "Context") + ".Consumer";
				case C:
					var n = e.render;
					return e = e.displayName, e ||= (e = n.displayName || n.name || "", e === "" ? "ForwardRef" : "ForwardRef(" + e + ")"), e;
				case E: return n = e.displayName || null, n === null ? t(e.type) || "Memo" : n;
				case D:
					n = e._payload, e = e._init;
					try {
						return t(e(n));
					} catch {}
			}
			return null;
		}
		function n(e) {
			return "" + e;
		}
		function r(e) {
			try {
				n(e);
				var t = !1;
			} catch {
				t = !0;
			}
			if (t) {
				t = console;
				var r = t.error, i = typeof Symbol == "function" && Symbol.toStringTag && e[Symbol.toStringTag] || e.constructor.name || "Object";
				return r.call(t, "The provided key is an unsupported type %s. This value must be coerced to a string before using it here.", i), n(e);
			}
		}
		function i(e) {
			if (e === v) return "<>";
			if (typeof e == "object" && e && e.$$typeof === D) return "<...>";
			try {
				var n = t(e);
				return n ? "<" + n + ">" : "<...>";
			} catch {
				return "<...>";
			}
		}
		function a() {
			var e = A.A;
			return e === null ? null : e.getOwner();
		}
		function o() {
			return Error("react-stack-top-frame");
		}
		function s(e) {
			if (j.call(e, "key")) {
				var t = Object.getOwnPropertyDescriptor(e, "key").get;
				if (t && t.isReactWarning) return !1;
			}
			return e.key !== void 0;
		}
		function c(e, t) {
			function n() {
				P || (P = !0, console.error("%s: `key` is not a prop. Trying to access it will result in `undefined` being returned. If you need to access the same value within the child component, you should pass it as a different prop. (https://react.dev/link/special-props)", t));
			}
			n.isReactWarning = !0, Object.defineProperty(e, "key", {
				get: n,
				configurable: !0
			});
		}
		function l() {
			var e = t(this.type);
			return F[e] || (F[e] = !0, console.error("Accessing element.ref was removed in React 19. ref is now a regular prop. It will be removed from the JSX Element type in a future release.")), e = this.props.ref, e === void 0 ? null : e;
		}
		function u(e, t, n, r, i, a) {
			var o = n.ref;
			return e = {
				$$typeof: h,
				type: e,
				key: t,
				props: n,
				_owner: r
			}, (o === void 0 ? null : o) === null ? Object.defineProperty(e, "ref", {
				enumerable: !1,
				value: null
			}) : Object.defineProperty(e, "ref", {
				enumerable: !1,
				get: l
			}), e._store = {}, Object.defineProperty(e._store, "validated", {
				configurable: !1,
				enumerable: !1,
				writable: !0,
				value: 0
			}), Object.defineProperty(e, "_debugInfo", {
				configurable: !1,
				enumerable: !1,
				writable: !0,
				value: null
			}), Object.defineProperty(e, "_debugStack", {
				configurable: !1,
				enumerable: !1,
				writable: !0,
				value: i
			}), Object.defineProperty(e, "_debugTask", {
				configurable: !1,
				enumerable: !1,
				writable: !0,
				value: a
			}), Object.freeze && (Object.freeze(e.props), Object.freeze(e)), e;
		}
		function d(e, n, i, o, l, d) {
			var p = n.children;
			if (p !== void 0) {
				if (o) {
					if (M(p)) {
						for (o = 0; o < p.length; o++) f(p[o]);
						Object.freeze && Object.freeze(p);
					} else console.error("React.jsx: Static children should always be an array. You are likely explicitly calling React.jsxs or React.jsxDEV. Use the Babel transform instead.");
				} else f(p);
			}
			if (j.call(n, "key")) {
				p = t(e);
				var m = Object.keys(n).filter(function(e) {
					return e !== "key";
				});
				o = 0 < m.length ? "{key: someKey, " + m.join(": ..., ") + ": ...}" : "{key: someKey}", R[p + o] || (m = 0 < m.length ? "{" + m.join(": ..., ") + ": ...}" : "{}", console.error("A props object containing a \"key\" prop is being spread into JSX:\n  let props = %s;\n  <%s {...props} />\nReact keys must be passed directly to JSX without using spread:\n  let props = %s;\n  <%s key={someKey} {...props} />", o, p, m, p), R[p + o] = !0);
			}
			if (p = null, i !== void 0 && (r(i), p = "" + i), s(n) && (r(n.key), p = "" + n.key), "key" in n) for (var h in i = {}, n) h !== "key" && (i[h] = n[h]);
			else i = n;
			return p && c(i, typeof e == "function" ? e.displayName || e.name || "Unknown" : e), u(e, p, i, a(), l, d);
		}
		function f(e) {
			p(e) ? e._store && (e._store.validated = 1) : typeof e == "object" && e && e.$$typeof === D && (e._payload.status === "fulfilled" ? p(e._payload.value) && e._payload.value._store && (e._payload.value._store.validated = 1) : e._store && (e._store.validated = 1));
		}
		function p(e) {
			return typeof e == "object" && !!e && e.$$typeof === h;
		}
		var m = _("react"), h = Symbol.for("react.transitional.element"), g = Symbol.for("react.portal"), v = Symbol.for("react.fragment"), y = Symbol.for("react.strict_mode"), b = Symbol.for("react.profiler"), x = Symbol.for("react.consumer"), S = Symbol.for("react.context"), C = Symbol.for("react.forward_ref"), w = Symbol.for("react.suspense"), T = Symbol.for("react.suspense_list"), E = Symbol.for("react.memo"), D = Symbol.for("react.lazy"), O = Symbol.for("react.activity"), k = Symbol.for("react.client.reference"), A = m.__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_USERS_THEY_CANNOT_UPGRADE, j = Object.prototype.hasOwnProperty, M = Array.isArray, N = console.createTask ? console.createTask : function() {
			return null;
		};
		m = { react_stack_bottom_frame: function(e) {
			return e();
		} };
		var P, F = {}, I = m.react_stack_bottom_frame.bind(m, o)(), L = N(i(o)), R = {};
		e.Fragment = v, e.jsx = function(e, t, n) {
			var r = 1e4 > A.recentlyCreatedOwnerStacks++;
			return d(e, t, n, !1, r ? Error("react-stack-top-frame") : I, r ? N(i(e)) : L);
		}, e.jsxs = function(e, t, n) {
			var r = 1e4 > A.recentlyCreatedOwnerStacks++;
			return d(e, t, n, !0, r ? Error("react-stack-top-frame") : I, r ? N(i(e)) : L);
		};
	})();
})), Y = (/* @__PURE__ */ g(((e, t) => {
	t.exports = process.env.NODE_ENV === "production" ? qe() : Je();
})))(), Ye = .1, Xe = 0, Ze = -1;
function Qe(e) {
	if (e === Ze) return Xe;
	let t = Ze < 0 ? 0 : Math.min((e - Ze) / 1e3, Ye);
	return Ze = e, Xe += t, Xe;
}
var $e = {
	thinking: "Thinking…",
	searching: "Searching…",
	working: "Working…",
	solving: "Solving…",
	listening: "Listening…",
	waiting: "Waiting…",
	generating: "Generating…"
};
function et({ logo: e, state: t = "thinking", size: n = 64, theme: r = "auto", tint: a, speed: o = 1, paused: s = !1, startAtMark: l = !1, bake: u, tune: d, onBake: f, style: p, "aria-label": m, ...h }) {
	let g = c(null), _ = Ve(r, g), v = He(), { points: y, error: b } = Ke(e, {
		count: ee(n, u?.style ?? "fill"),
		...u
	}), x = c(f);
	return x.current = f, i(() => {
		(y || b) && x.current?.(y, b);
	}, [y, b]), i(() => {
		let e = g.current;
		if (!e || !y) return;
		let r = Math.min(2, typeof devicePixelRatio < "u" && devicePixelRatio || 1);
		e.width = Math.round(n * r), e.height = Math.round(n * r);
		let i = e.getContext("2d");
		if (!i) return;
		let { frame: c, speed: u, opts: f, binding: p } = Re(t, y, d), m = typeof f.dwell == "number" ? f.dwell : 5.5, h = typeof f.morph == "number" ? f.morph : 1.9, b = l ? m + h : 0, x = a ? le(a) : null, S = x ? de(x, _) : null, C = u * o, w = (e) => {
			i.setTransform(r, 0, 0, r, 0, 0), i.clearRect(0, 0, n, n);
			let t = c(n, e, f, p);
			S ? pe(i, t, _, S) : ce(i, t, _);
		};
		if (v) {
			w(b || 4.2);
			return;
		}
		let T = 0, E = !1, D = (e) => {
			w(Qe(e) * C + b), E && (T = requestAnimationFrame(D));
		}, O = () => {
			E || s || (E = !0, T = requestAnimationFrame(D));
		}, k = () => {
			E = !1, cancelAnimationFrame(T);
		};
		w(Xe * C + b);
		let A = !0, j = typeof IntersectionObserver < "u" ? new IntersectionObserver(([e]) => {
			A = e.isIntersecting, A && document.visibilityState !== "hidden" ? O() : k();
		}) : null;
		j?.observe(e);
		let M = () => {
			document.visibilityState === "hidden" ? k() : A && O();
		};
		return document.addEventListener("visibilitychange", M), j || O(), () => {
			k(), j?.disconnect(), document.removeEventListener("visibilitychange", M);
		};
	}, [
		y,
		t,
		n,
		_,
		a,
		o,
		s,
		v,
		d,
		l
	]), /* @__PURE__ */ (0, Y.jsx)("canvas", {
		ref: g,
		role: "img",
		"aria-label": m ?? $e[t],
		style: {
			width: n,
			height: n,
			display: "block",
			...p
		},
		...h
	});
}
//#endregion
//#region src/components/Brand.tsx
var tt = {
	id: "01-nova",
	title: "Nova",
	logoSrc: "/brand-logo.svg",
	loaderSrc: "/brand-loader-mark.svg",
	tint: "#4f8cff"
}, nt = e(tt);
function rt({ brand: e = tt, children: t }) {
	return /* @__PURE__ */ (0, Y.jsx)(nt.Provider, {
		value: e,
		children: t
	});
}
function it() {
	return r(nt);
}
function at({ size: e = 40, className: t = "", alt: n }) {
	let r = it();
	return /* @__PURE__ */ (0, Y.jsx)("img", {
		className: `lf-brand ${t}`,
		src: r.logoSrc,
		width: e,
		height: e,
		alt: n ?? r.title
	});
}
function ot({ size: e = 20, state: t = "working", className: n = "", ...r }) {
	let a = it(), o = p(), [s, c] = l(null);
	return i(() => {
		let e = !0;
		return fetch(a.loaderSrc).then((e) => {
			if (!e.ok) throw Error(`Logo ${e.status}`);
			return e.text();
		}).then((t) => e && c(t)).catch(() => e && c(null)), () => {
			e = !1;
		};
	}, [a.loaderSrc]), /* @__PURE__ */ (0, Y.jsx)("span", {
		className: `lf-brand-loader ${n}`,
		style: {
			width: e,
			height: e
		},
		children: /* @__PURE__ */ (0, Y.jsx)(u, {
			mode: "wait",
			initial: !1,
			children: s && !o ? /* @__PURE__ */ (0, Y.jsx)(d.span, {
				initial: { opacity: 0 },
				animate: { opacity: 1 },
				exit: { opacity: 0 },
				children: /* @__PURE__ */ (0, Y.jsx)(et, {
					logo: { svg: s },
					size: e,
					state: t,
					tint: a.tint,
					...r
				})
			}, "thinking") : /* @__PURE__ */ (0, Y.jsx)(d.img, {
				src: a.loaderSrc,
				alt: "",
				width: e,
				height: e,
				animate: o ? void 0 : { opacity: [
					.45,
					1,
					.45
				] },
				transition: {
					duration: 1.25,
					repeat: Infinity
				}
			}, "mark")
		})
	});
}
//#endregion
//#region src/motion/presets.ts
var X = {
	instant: .12,
	fast: .2,
	base: .32,
	slow: .48,
	easeOut: [
		.16,
		1,
		.3,
		1
	],
	easeStandard: [
		.22,
		1,
		.36,
		1
	],
	spring: {
		type: "spring",
		stiffness: 360,
		damping: 30
	},
	springSoft: {
		type: "spring",
		stiffness: 220,
		damping: 25
	},
	springSnappy: {
		type: "spring",
		stiffness: 520,
		damping: 34
	}
}, st = { scale: .97 }, ct = { y: -2 };
//#endregion
//#region src/components/Primitives.tsx
function lt({ children: e, className: t = "" }) {
	return /* @__PURE__ */ (0, Y.jsx)("section", {
		className: `lf-surface ${t}`,
		children: e
	});
}
function ut({ variant: e = "primary", size: t = "md", className: n = "", children: r, ...i }) {
	return /* @__PURE__ */ (0, Y.jsx)(d.button, {
		whileTap: i.disabled ? void 0 : st,
		className: `lf-button lf-button--${e} lf-button--${t} ${n}`,
		...i,
		children: r
	});
}
function dt({ label: e, children: t, className: n = "", ...r }) {
	return /* @__PURE__ */ (0, Y.jsx)(d.button, {
		type: "button",
		whileTap: st,
		className: `lf-icon-button ${n}`,
		"aria-label": e,
		...r,
		children: t
	});
}
function ft({ state: e = "idle", idleLabel: t = "Продолжить", pendingLabel: n = "Собираем…", successLabel: r = "Готово", errorLabel: i = "Повторить", children: a, ...o }) {
	let s = e === "pending" ? /* @__PURE__ */ (0, Y.jsxs)(Y.Fragment, { children: [/* @__PURE__ */ (0, Y.jsx)(ot, {
		state: "working",
		size: 20
	}), n] }) : e === "success" ? /* @__PURE__ */ (0, Y.jsxs)(Y.Fragment, { children: ["✓ ", r] }) : e === "error" ? /* @__PURE__ */ (0, Y.jsxs)(Y.Fragment, { children: ["↻ ", i] }) : a ?? t;
	return /* @__PURE__ */ (0, Y.jsx)(ut, {
		disabled: e === "pending" || o.disabled,
		...o,
		children: /* @__PURE__ */ (0, Y.jsx)(u, {
			mode: "wait",
			initial: !1,
			children: /* @__PURE__ */ (0, Y.jsx)(d.span, {
				className: "lf-button-face",
				initial: {
					opacity: 0,
					y: 5,
					filter: "blur(4px)"
				},
				animate: {
					opacity: 1,
					y: 0,
					filter: "blur(0px)"
				},
				exit: {
					opacity: 0,
					y: -5,
					filter: "blur(4px)"
				},
				transition: { duration: X.fast },
				children: s
			}, e)
		})
	});
}
function pt({ items: e, value: t, onChange: n, label: r = "Выбор" }) {
	let i = Math.max(0, e.findIndex((e) => e.value === t));
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "lf-segmented",
		role: "radiogroup",
		"aria-label": r,
		style: { gridTemplateColumns: `repeat(${e.length},1fr)` },
		children: [/* @__PURE__ */ (0, Y.jsx)(d.span, {
			className: "lf-segment-pill",
			"aria-hidden": !0,
			style: { width: `calc((100% - 6px) / ${e.length})` },
			animate: { x: `${i * 100}%` },
			transition: X.spring
		}), e.map((e) => /* @__PURE__ */ (0, Y.jsx)("button", {
			className: "lf-segment",
			role: "radio",
			"aria-checked": e.value === t,
			onClick: () => n(e.value),
			children: e.label
		}, e.value))]
	});
}
function mt({ value: e, min: t = 0, max: n = 100, step: r = 1, detents: i = [], onChange: o, label: s = "Значение" }) {
	let c = a();
	return /* @__PURE__ */ (0, Y.jsxs)("div", {
		className: "lf-slider",
		children: [
			/* @__PURE__ */ (0, Y.jsx)("label", {
				htmlFor: c,
				children: s
			}),
			/* @__PURE__ */ (0, Y.jsx)("input", {
				id: c,
				type: "range",
				min: t,
				max: n,
				step: r,
				value: e,
				onChange: (e) => o(Number(e.target.value))
			}),
			i.length > 0 && /* @__PURE__ */ (0, Y.jsx)("div", {
				className: "lf-detents",
				children: i.map((e) => /* @__PURE__ */ (0, Y.jsx)("span", { children: e }, e))
			})
		]
	});
}
function ht({ checked: e, onChange: t, label: n }) {
	return /* @__PURE__ */ (0, Y.jsx)("button", {
		type: "button",
		role: "switch",
		"aria-checked": e,
		"aria-label": n,
		className: "lf-toggle",
		"data-on": e,
		onClick: () => t(!e),
		children: /* @__PURE__ */ (0, Y.jsx)(d.span, {
			className: "lf-toggle-knob",
			animate: { x: e ? 18 : 0 },
			transition: X.springSnappy
		})
	});
}
function gt({ title: e, children: t, defaultOpen: n = !1 }) {
	let [r, i] = l(n);
	return /* @__PURE__ */ (0, Y.jsxs)("div", { children: [/* @__PURE__ */ (0, Y.jsxs)("button", {
		className: "lf-button lf-button--ghost",
		"aria-expanded": r,
		onClick: () => i((e) => !e),
		children: [e, /* @__PURE__ */ (0, Y.jsx)(d.span, {
			animate: { rotate: r ? 180 : 0 },
			children: "⌄"
		})]
	}), /* @__PURE__ */ (0, Y.jsx)(u, {
		initial: !1,
		children: r && /* @__PURE__ */ (0, Y.jsx)(d.div, {
			initial: {
				height: 0,
				opacity: 0
			},
			animate: {
				height: "auto",
				opacity: 1
			},
			exit: {
				height: 0,
				opacity: 0
			},
			transition: {
				duration: X.base,
				ease: X.easeOut
			},
			style: { overflow: "hidden" },
			children: t
		})
	})] });
}
//#endregion
//#region src/components/MotionKit.tsx
function _t({ children: e, className: t = "" }) {
	let n = p();
	return /* @__PURE__ */ (0, Y.jsx)("span", {
		className: t,
		"aria-label": e,
		children: e.split("").map((e, t) => /* @__PURE__ */ (0, Y.jsx)(d.span, {
			"aria-hidden": !0,
			className: "lf-reveal-char",
			initial: !n && {
				opacity: 0,
				filter: "blur(8px)",
				y: 7
			},
			animate: {
				opacity: 1,
				filter: "blur(0px)",
				y: 0
			},
			transition: n ? { duration: 0 } : {
				delay: t * .018,
				duration: .3
			},
			children: e === " " ? "\xA0" : e
		}, `${e}-${t}`))
	});
}
function vt({ children: e, delay: t = 0, className: n = "" }) {
	let r = p();
	return /* @__PURE__ */ (0, Y.jsx)(d.div, {
		className: n,
		initial: !r && {
			opacity: 0,
			y: 14
		},
		animate: {
			opacity: 1,
			y: 0
		},
		transition: r ? { duration: 0 } : {
			duration: .45,
			delay: t,
			ease: X.easeOut
		},
		children: e
	});
}
function yt({ children: e, active: t = !1, onClick: n, className: r = "" }) {
	let i = c(null), a = p(), o = f(0), s = f(0), l = m(h(s, [-.5, .5], [4, -4]), X.springSoft), u = m(h(o, [-.5, .5], [-4, 4]), X.springSoft);
	return /* @__PURE__ */ (0, Y.jsx)(d.button, {
		ref: i,
		type: "button",
		className: `lf-tilt ${r}`,
		"data-active": t,
		style: a ? void 0 : {
			rotateX: l,
			rotateY: u,
			transformPerspective: 800
		},
		onPointerMove: (e) => {
			if (a || !i.current) return;
			let t = i.current.getBoundingClientRect();
			o.set((e.clientX - t.left) / t.width - .5), s.set((e.clientY - t.top) / t.height - .5);
		},
		onPointerLeave: () => {
			o.set(0), s.set(0);
		},
		onClick: n,
		"aria-pressed": t,
		children: e
	});
}
function bt({ children: e, className: t = "", ...n }) {
	let r = c(null), i = p(), a = m(0, {
		stiffness: 180,
		damping: 18
	}), o = m(0, {
		stiffness: 180,
		damping: 18
	});
	return /* @__PURE__ */ (0, Y.jsx)(d.button, {
		...n,
		ref: r,
		className: t,
		style: i ? void 0 : {
			x: a,
			y: o
		},
		onPointerMove: (e) => {
			if (i || !r.current) return;
			let t = r.current.getBoundingClientRect();
			a.set((e.clientX - t.left - t.width / 2) * .13), o.set((e.clientY - t.top - t.height / 2) * .13);
		},
		onPointerLeave: () => {
			a.set(0), o.set(0);
		},
		children: e
	});
}
function xt({ items: e, value: t, onChange: n, label: r = "Палитра" }) {
	return /* @__PURE__ */ (0, Y.jsx)("div", {
		className: "lf-swatches",
		role: "radiogroup",
		"aria-label": r,
		children: e.map((e) => /* @__PURE__ */ (0, Y.jsx)(d.button, {
			type: "button",
			role: "radio",
			"aria-label": e.name,
			"aria-checked": e.id === t,
			className: "lf-swatch",
			style: { background: `linear-gradient(145deg,${e.colors[0]},${e.colors[1]})` },
			whileTap: { scale: .9 },
			onClick: () => n(e.id)
		}, e.id))
	});
}
function St() {
	let e = p();
	return /* @__PURE__ */ (0, Y.jsxs)("span", {
		className: "lf-fluid-orbit",
		"aria-hidden": !0,
		children: [/* @__PURE__ */ (0, Y.jsx)("i", {}), /* @__PURE__ */ (0, Y.jsx)(d.b, {
			animate: e ? void 0 : { rotate: 360 },
			transition: {
				duration: 1.8,
				repeat: Infinity,
				ease: "linear"
			},
			children: /* @__PURE__ */ (0, Y.jsx)("i", {})
		})]
	});
}
//#endregion
//#region src/vendor/morphicons/core/interpolate.ts
function Ct(e) {
	return e.items.map(() => new Float64Array(2 * e.n));
}
function wt(e, t, n) {
	for (let r = 0; r < e.items.length; r++) {
		let i = e.items[r], a = n[r], o = e.n, s = Math.exp(i.lnSigma * t), c = i.theta * t, l = Math.cos(c) * s, u = Math.sin(c) * s, d, f;
		if (i.block) {
			let [e, n] = i.block.off, [r, a] = i.block.drift;
			d = i.ca[0] + r * t + (e * l - n * u - e), f = i.ca[1] + a * t + (e * u + n * l - n);
		} else d = i.ca[0] + (i.cb[0] - i.ca[0]) * t, f = i.ca[1] + (i.cb[1] - i.ca[1]) * t;
		for (let e = 0; e < o; e++) {
			let n = i.aC[2 * e] + (i.bT[2 * e] - i.aC[2 * e]) * t, r = i.aC[2 * e + 1] + (i.bT[2 * e + 1] - i.aC[2 * e + 1]) * t;
			a[2 * e] = d + n * l - r * u, a[2 * e + 1] = f + n * u + r * l;
		}
	}
}
//#endregion
//#region src/vendor/morphicons/core/plan.ts
var Tt = .35, Et = .05, Dt = .005, Ot = 8, kt = 1e5;
function At(e) {
	let t = e.length / 2, n = 0, r = 0;
	for (let i = 0; i < t; i++) n += e[2 * i], r += e[2 * i + 1];
	return [n / t, r / t];
}
function jt(e) {
	let t = e.length / 2, n = 0;
	for (let r = 1; r < t; r++) n += Math.hypot(e[2 * r] - e[2 * r - 2], e[2 * r + 1] - e[2 * r - 1]);
	return n;
}
function Mt(e) {
	let t = e.length / 2, n = new Float64Array(2 * t);
	for (let r = 0; r < t; r++) n[2 * r] = e[2 * (t - 1 - r)], n[2 * r + 1] = e[2 * (t - 1 - r) + 1];
	return n;
}
function Nt(e, t) {
	let n = e.length / 2, r = new Float64Array(2 * n);
	for (let i = 0; i < n; i++) {
		let a = (i + t) % n;
		r[2 * i] = e[2 * a], r[2 * i + 1] = e[2 * a + 1];
	}
	return r;
}
function Pt(e, t, n, r) {
	let i = e.length / 2, a = 0, o = 0, s = 0, c = 0, l = 0, u = 0;
	for (let d = 0; d < i; d++) {
		let i = e[2 * d] - n[0], f = e[2 * d + 1] - n[1], p = t[2 * d] - r[0], m = t[2 * d + 1] - r[1];
		a += i * p, c += f * m, o += i * m, s += f * p, l += i * i + f * f, u += p * p + m * m;
	}
	let d = Math.atan2(o - s, a + c), f = Math.cos(d) * (a + c) + Math.sin(d) * (o - s), p = l > 1e-12 ? f / l : 1;
	p > 1e-6 || (p = 1e-6);
	let m = Math.max(0, p * p * l - 2 * p * f + u), h = u > 1e-12 ? Math.sqrt(m / u) : 0;
	return {
		theta: d,
		sigma: p,
		res: h
	};
}
function Ft(e, t, n = !1, r = !1) {
	let i = At(e), a = At(t), o = n && !r, s = o ? e : t, c = n || r ? s.length / 2 : 1, l = Infinity, u = s, d = {
		theta: 0,
		sigma: 1,
		res: 0
	};
	for (let n = 0; n < 2; n++) {
		let r = n ? Mt(s) : s;
		for (let n = 0; n < c; n++) {
			let s = n ? Nt(r, n) : r, c = o ? Pt(s, t, i, a) : Pt(e, s, i, a), f = c.res + Et * Math.abs(c.theta) / Math.PI;
			f < l && (l = f, u = s, d = c);
		}
	}
	return o ? {
		ca: i,
		cb: a,
		a: u,
		b: t,
		...d
	} : {
		ca: i,
		cb: a,
		a: e,
		b: u,
		...d
	};
}
function It(e, t) {
	let n = t.map(At), r = t.map(jt);
	return e.map((e) => {
		let t = At(e), i = jt(e);
		return n.map((e, n) => Math.hypot(t[0] - e[0], t[1] - e[1]) + Tt * Math.abs(i - r[n]));
	});
}
function Lt(e) {
	let t = e.length;
	if (t > Ot) {
		let n = [];
		for (let r = 0; r < t; r++) for (let i = 0; i < t; i++) n.push([
			e[r][i],
			r,
			i
		]);
		n.sort((e, t) => e[0] - t[0]);
		let r = Array(t).fill(-1), i = Array(t).fill(!1);
		for (let [, e, t] of n) r[e] < 0 && !i[t] && (r[e] = t, i[t] = !0);
		return r;
	}
	let n = Array.from({ length: t }, (e, t) => t), r = n.slice(), i = Infinity, a = (n, o, s) => {
		if (!(s >= i)) {
			if (o === t) {
				i = s, r = n.slice();
				return;
			}
			for (let r = o; r < t; r++) [n[o], n[r]] = [n[r], n[o]], a(n, o + 1, s + e[o][n[o]]), [n[o], n[r]] = [n[r], n[o]];
		}
	};
	return a(n, 0, 0), r;
}
function Rt(e) {
	let t = e.length, n = e[0].length;
	if (n ** t > kt) {
		let r = e.map((e) => {
			let t = 0;
			for (let n = 1; n < e.length; n++) e[n] < e[t] && (t = n);
			return t;
		}), i = Array(n).fill(0);
		for (let e of r) i[e]++;
		for (let a = 0; a < n; a++) {
			if (i[a] > 0) continue;
			let n = -1, o = Infinity;
			for (let s = 0; s < t; s++) {
				if (i[r[s]] < 2) continue;
				let t = e[s][a] - e[s][r[s]];
				t < o && (o = t, n = s);
			}
			i[r[n]]--, r[n] = a, i[a]++;
		}
		return r;
	}
	let r = null, i = Infinity, a = Array(t), o = Array(n).fill(0), s = (c, l, u) => {
		if (!(l >= i || n - u > t - c)) {
			if (c === t) {
				i = l, r = a.slice();
				return;
			}
			for (let t = 0; t < n; t++) a[c] = t, o[t]++, s(c + 1, l + e[c][t], u + +(o[t] === 1)), o[t]--;
		}
	};
	if (s(0, 0, 0), !r) throw Error("morphicons: no valid surjection (B < S)");
	return r;
}
function zt(e, t) {
	let n = e.length * t, r = new Float64Array(2 * n), i = new Float64Array(2 * n);
	e.forEach((e, n) => {
		r.set(e.a, 2 * t * n), i.set(e.bO, 2 * t * n);
	});
	let a = At(r), o = Pt(r, i, a, At(i));
	if (o.res >= Dt) return;
	let s = Math.cos(-o.theta), c = Math.sin(-o.theta), l = Math.cos(o.theta), u = Math.sin(o.theta);
	for (let n of e) {
		let e = 0, r = 0;
		for (let i = 0; i < t; i++) {
			let t = n.bO[2 * i] - n.cb[0], a = n.bO[2 * i + 1] - n.cb[1];
			n.bT[2 * i] = (t * s - a * c) / o.sigma, n.bT[2 * i + 1] = (t * c + a * s) / o.sigma;
			let d = o.sigma * (l * n.aC[2 * i] - u * n.aC[2 * i + 1]) - t, f = o.sigma * (u * n.aC[2 * i] + l * n.aC[2 * i + 1]) - a;
			e += d * d + f * f, r += t * t + a * a;
		}
		n.theta = o.theta, n.lnSigma = Math.log(o.sigma), n.res = r > 1e-12 ? Math.sqrt(e / r) : 0;
		let i = Math.exp(n.lnSigma), d = Math.cos(n.theta) * i, f = Math.sin(n.theta) * i, p = n.ca[0] - a[0], m = n.ca[1] - a[1], h = p * d - m * f - p, g = p * f + m * d - m;
		n.block = {
			off: [p, m],
			drift: [n.cb[0] - n.ca[0] - h, n.cb[1] - n.ca[1] - g]
		};
	}
}
function Bt(e, t) {
	let n = e.length, r = t.length;
	if (n === 0 || r === 0) throw Error("morphicons: icon has no subpaths");
	let i = e.map((e) => e.pts), a = t.map((e) => e.pts), o = [];
	if (n === r) {
		let e = Lt(It(i, a));
		for (let t = 0; t < n; t++) o.push([t, e[t]]);
	} else if (n < r) {
		let e = Rt(It(a, i));
		for (let t = 0; t < r; t++) o.push([e[t], t]);
	} else {
		let e = Rt(It(i, a));
		for (let t = 0; t < n; t++) o.push([t, e[t]]);
	}
	let s = i[0].length / 2, c = o.map(([n, r]) => {
		let o = Ft(i[n], a[r], e[n].closed, t[r].closed), c = o.a, l = new Float64Array(2 * s), u = new Float64Array(2 * s), d = new Float64Array(2 * s), f = Math.cos(-o.theta), p = Math.sin(-o.theta);
		for (let e = 0; e < s; e++) {
			l[2 * e] = c[2 * e] - o.ca[0], l[2 * e + 1] = c[2 * e + 1] - o.ca[1];
			let t = o.b[2 * e] - o.cb[0], n = o.b[2 * e + 1] - o.cb[1];
			u[2 * e] = (t * f - n * p) / o.sigma, u[2 * e + 1] = (t * p + n * f) / o.sigma, d[2 * e] = o.b[2 * e], d[2 * e + 1] = o.b[2 * e + 1];
		}
		return {
			a: c,
			aC: l,
			bT: u,
			bO: d,
			ca: o.ca,
			cb: o.cb,
			theta: o.theta,
			lnSigma: Math.log(o.sigma),
			res: o.res,
			closed: e[n].closed && t[r].closed,
			block: null
		};
	});
	return c.length > 1 && zt(c, s), {
		items: c,
		n: s
	};
}
//#endregion
//#region src/vendor/morphicons/core/parse.ts
var Vt = "MmLlHhVvCcSsQqTtAaZz";
function Ht(e) {
	let t = [], n = e.length, r = 0, i = 0, a = 0, o = 0, s = 0, c = null, l = "", u = 0, d = 0, f = "", p = !1, m = (e) => {
		throw Error(`morphicons: ${e} at d[${r}]`);
	}, h = (e) => e >= 48 && e <= 57, g = () => {
		for (; r < n;) {
			let t = e.charCodeAt(r);
			if (t === 32 || t === 9 || t === 10 || t === 13 || t === 12 || t === 44) r++;
			else break;
		}
	}, _ = () => {
		g();
		let t = r;
		r < n && (e[r] === "+" || e[r] === "-") && r++;
		let i = !1;
		for (; r < n && h(e.charCodeAt(r));) r++, i = !0;
		if (r < n && e[r] === ".") for (r++; r < n && h(e.charCodeAt(r));) r++, i = !0;
		if (i || m("expected number"), r < n && (e[r] === "e" || e[r] === "E")) {
			let t = r;
			r++, r < n && (e[r] === "+" || e[r] === "-") && r++;
			let i = !1;
			for (; r < n && h(e.charCodeAt(r));) r++, i = !0;
			i || (r = t);
		}
		return Number(e.slice(t, r));
	}, v = () => {
		g();
		let t = e[r];
		return t === "0" || t === "1" ? (r++, +(t === "1")) : m("expected arc flag (0|1)");
	}, y = () => (p || m("path must start with M/m"), c || (c = {
		x0: i,
		y0: a,
		segs: [],
		closed: !1
	}, t.push(c)), c), b = !1, x = () => _() + (b ? i : 0), S = () => _() + (b ? a : 0);
	for (; g(), !(r >= n);) {
		let n = e[r];
		switch (Vt.includes(n) ? (l = n, r++) : l === "" ? m("path must start with M/m") : l === "M" ? l = "L" : l === "m" ? l = "l" : (l === "Z" || l === "z") && m("stray data after Z"), b = l >= "a", b ? l.toUpperCase() : l) {
			case "M": {
				p = !0;
				let e = x(), n = S();
				i = e, a = n, o = e, s = n, c = {
					x0: e,
					y0: n,
					segs: [],
					closed: !1
				}, t.push(c), f = "";
				break;
			}
			case "L": {
				let e = x(), t = S();
				y().segs.push([
					"L",
					e,
					t
				]), i = e, a = t, f = "";
				break;
			}
			case "H": {
				let e = x();
				y().segs.push([
					"L",
					e,
					a
				]), i = e, f = "";
				break;
			}
			case "V": {
				let e = S();
				y().segs.push([
					"L",
					i,
					e
				]), a = e, f = "";
				break;
			}
			case "C":
			case "S": {
				let e, t;
				l === "C" || l === "c" ? (e = x(), t = S()) : (e = f === "C" ? 2 * i - u : i, t = f === "C" ? 2 * a - d : a);
				let n = x(), r = S(), o = x(), s = S();
				y().segs.push([
					"C",
					e,
					t,
					n,
					r,
					o,
					s
				]), u = n, d = r, i = o, a = s, f = "C";
				break;
			}
			case "Q":
			case "T": {
				let e, t;
				l === "Q" || l === "q" ? (e = x(), t = S()) : (e = f === "Q" ? 2 * i - u : i, t = f === "Q" ? 2 * a - d : a);
				let n = x(), r = S();
				y().segs.push([
					"Q",
					e,
					t,
					n,
					r
				]), u = e, d = t, i = n, a = r, f = "Q";
				break;
			}
			case "A": {
				let e = _(), t = _(), n = _(), r = v(), o = v(), s = x(), c = S();
				y().segs.push([
					"A",
					e,
					t,
					n,
					r,
					o,
					s,
					c
				]), i = s, a = c, f = "";
				break;
			}
			case "Z":
				c &&= (c.closed = !0, null), i = o, a = s, f = "";
				break;
			default: m(`unsupported command "${l}"`);
		}
	}
	return t.filter((e) => e.segs.length > 0);
}
//#endregion
//#region src/vendor/morphicons/core/serialize.ts
function Ut(e) {
	return String(Math.round(e * 100) / 100);
}
function Wt(e, t) {
	let n = "";
	for (let r = 0; r < e.length; r++) {
		let i = e[r], a = i.length / 2;
		n += `M${Ut(i[0])} ${Ut(i[1])}`;
		for (let e = 1; e < a; e++) n += `L${Ut(i[2 * e])} ${Ut(i[2 * e + 1])}`;
		t?.[r] && (n += "Z");
	}
	return n;
}
function Z(e) {
	return String(Math.round(e * 1e4) / 1e4);
}
function Gt(e) {
	let t = "";
	for (let { pts: n, closed: r } of e) {
		t += `M${Z(n[0])} ${Z(n[1])}`;
		for (let e = 2; e < n.length; e += 6) t += `C${Z(n[e])} ${Z(n[e + 1])} ${Z(n[e + 2])} ${Z(n[e + 3])} ${Z(n[e + 4])} ${Z(n[e + 5])}`;
		r && (t += "Z");
	}
	return t;
}
//#endregion
//#region src/vendor/morphicons/core/normalize.ts
var Kt = 4 / 3 * Math.tan(Math.PI / 8), qt = 2 * Math.PI;
function Jt(e, t) {
	let n = [e, t], r = e, i = t, a = (e, t, a, o, s, c) => {
		n.push(e, t, a, o, s, c), r = s, i = c;
	}, o = (e, t) => {
		Math.abs(e - r) < 1e-12 && Math.abs(t - i) < 1e-12 || a(r + (e - r) / 3, i + (t - i) / 3, r + 2 * (e - r) / 3, i + 2 * (t - i) / 3, e, t);
	};
	return [
		a,
		o,
		(e, t, n, o) => {
			a(r + 2 / 3 * (e - r), i + 2 / 3 * (t - i), n + 2 / 3 * (e - n), o + 2 / 3 * (t - o), n, o);
		},
		(e, t, n, s, c, l, u) => {
			let d = r, f = i;
			if (Math.abs(l - d) < 1e-12 && Math.abs(u - f) < 1e-12) return;
			let p = Math.abs(e), m = Math.abs(t);
			if (p < 1e-12 || m < 1e-12) {
				o(l, u);
				return;
			}
			let h = n * Math.PI / 180, g = Math.cos(h), _ = Math.sin(h), v = (d - l) / 2, y = (f - u) / 2, b = g * v + _ * y, x = -_ * v + g * y, S = b * b / (p * p) + x * x / (m * m);
			if (S > 1) {
				let e = Math.sqrt(S);
				p *= e, m *= e;
			}
			let C = p * p, w = m * m, T = b * b, E = x * x, D = (C * w - C * E - w * T) / (C * E + w * T);
			D < 0 && (D = 0);
			let O = (s === c ? -1 : 1) * Math.sqrt(D), k = O * p * x / m, A = -O * m * b / p, j = g * k - _ * A + (d + l) / 2, M = _ * k + g * A + (f + u) / 2, N = Math.atan2((x - A) / m, (b - k) / p), P = Math.atan2((-x - A) / m, (-b - k) / p) - N;
			c === 0 && P > 0 ? P -= qt : c === 1 && P < 0 && (P += qt);
			let F = Math.max(1, Math.ceil(Math.abs(P) / (Math.PI / 2) - 1e-9)), I = P / F, L = 4 / 3 * Math.tan(I / 4), R = (e) => j + p * Math.cos(e) * g - m * Math.sin(e) * _, z = (e) => M + p * Math.cos(e) * _ + m * Math.sin(e) * g, B = (e) => -p * Math.sin(e) * g - m * Math.cos(e) * _, V = (e) => -p * Math.sin(e) * _ + m * Math.cos(e) * g, ee = N, te = d, ne = f;
			for (let e = 1; e <= F; e++) {
				let t = N + I * e, n = e === F ? l : R(t), r = e === F ? u : z(t);
				a(te + L * B(ee), ne + L * V(ee), n - L * B(t), r - L * V(t), n, r), ee = t, te = n, ne = r;
			}
		},
		(e) => (e && o(n[0], n[1]), n.length < 8 ? null : {
			pts: Float64Array.from(n),
			closed: e
		})
	];
}
function Yt(e) {
	let [t, n, r, i, a] = Jt(e.x0, e.y0);
	for (let a of e.segs) switch (a[0]) {
		case "L":
			n(a[1], a[2]);
			break;
		case "C":
			t(a[1], a[2], a[3], a[4], a[5], a[6]);
			break;
		case "Q":
			r(a[1], a[2], a[3], a[4]);
			break;
		case "A": i(a[1], a[2], a[3], a[4], a[5], a[6], a[7]);
	}
	return a(e.closed);
}
function Q(e, t, n = 0) {
	let r = e[t];
	if (r === void 0) return n;
	let i = typeof r == "number" ? r : Number(r);
	return Number.isFinite(i) ? i : n;
}
function Xt(e) {
	let t = String(e ?? "").trim();
	if (!t) return [];
	let n = t.split(/[\s,]+/).map(Number);
	if (n.some((e) => !Number.isFinite(e))) throw Error(`morphicons: invalid points: "${t}"`);
	return n;
}
function Zt(e, t) {
	if (e.length < 4) return null;
	let [, n, , , r] = Jt(e[0], e[1]);
	for (let t = 2; t + 1 < e.length; t += 2) n(e[t], e[t + 1]);
	return r(t);
}
function Qt(e, t, n, r) {
	if (n < 1e-12 || r < 1e-12) return null;
	let i = Kt * n, a = Kt * r, o = e + n, s = e - n, c = t + r, l = t - r, [u, , , , d] = Jt(o, t);
	return u(o, t + a, e + i, c, e, c), u(e - i, c, s, t + a, s, t), u(s, t - a, e - i, l, e, l), u(e + i, l, o, t - a, o, t), d(!0);
}
function $t(e) {
	let t = Q(e, "x"), n = Q(e, "y"), r = Q(e, "width"), i = Q(e, "height");
	if (r < 1e-12 || i < 1e-12) return null;
	let a = Q(e, "rx", NaN), o = Q(e, "ry", NaN);
	if (Number.isNaN(a) && (a = Number.isNaN(o) ? 0 : o), Number.isNaN(o) && (o = a), a = Math.min(Math.max(a, 0), r / 2), o = Math.min(Math.max(o, 0), i / 2), a < 1e-12 || o < 1e-12) return Zt([
		t,
		n,
		t + r,
		n,
		t + r,
		n + i,
		t,
		n + i
	], !0);
	let s = t + a, c = t + r - a, l = t + r, u = n + o, d = n + i - o, f = n + i, p = Kt * a, m = Kt * o, [h, g, , , _] = Jt(s, n);
	return g(c, n), h(c + p, n, l, u - m, l, u), g(l, d), h(l, d + m, c + p, f, c, f), g(s, f), h(s - p, f, t, d + m, t, d), g(t, u), h(t, u - m, s - p, n, s, n), _(!0);
}
function en(e) {
	let t = [], n = (e) => {
		e && t.push(e);
	};
	if (typeof e == "string") {
		for (let t of Ht(e)) n(Yt(t));
		return t;
	}
	for (let [t, r] of e) switch (t) {
		case "path":
			for (let e of Ht(String(r.d ?? ""))) n(Yt(e));
			break;
		case "line": {
			let [, e, , , t] = Jt(Q(r, "x1"), Q(r, "y1"));
			e(Q(r, "x2"), Q(r, "y2")), n(t(!1));
			break;
		}
		case "circle": {
			let e = Q(r, "r");
			n(Qt(Q(r, "cx"), Q(r, "cy"), e, e));
			break;
		}
		case "ellipse":
			n(Qt(Q(r, "cx"), Q(r, "cy"), Q(r, "rx"), Q(r, "ry")));
			break;
		case "rect":
			n($t(r));
			break;
		case "polyline":
			n(Zt(Xt(r.points), !1));
			break;
		case "polygon":
			n(Zt(Xt(r.points), !0));
			break;
		default: throw Error(`morphicons: unsupported tag <${t}>`);
	}
	return t;
}
//#endregion
//#region src/vendor/morphicons/core/resample.ts
var tn = Math.PI / 8, nn = [
	.18343464249564978,
	.525532409916329,
	.7966664774136267,
	.9602898564975363
], rn = [
	.362683783378362,
	.31370664587788727,
	.22238103445337448,
	.10122853629037626
];
function an(e, t, n) {
	let r = 6 * t, i = 1 - n, a = 3 * i * i, o = 6 * i * n, s = 3 * n * n, c = a * (e[r + 2] - e[r]) + o * (e[r + 4] - e[r + 2]) + s * (e[r + 6] - e[r + 4]), l = a * (e[r + 3] - e[r + 1]) + o * (e[r + 5] - e[r + 3]) + s * (e[r + 7] - e[r + 5]);
	return Math.hypot(c, l);
}
function on(e, t, n = 1) {
	let r = n / 2, i = 0;
	for (let n = 0; n < 4; n++) i += rn[n] * (an(e, t, r + r * nn[n]) + an(e, t, r - r * nn[n]));
	return i * r;
}
function sn(e, t, n, r, i) {
	let a = 6 * t, o = 1 - n, s = o * o * o, c = 3 * o * o * n, l = 3 * o * n * n, u = n * n * n;
	r[i] = s * e[a] + c * e[a + 2] + l * e[a + 4] + u * e[a + 6], r[i + 1] = s * e[a + 1] + c * e[a + 3] + l * e[a + 5] + u * e[a + 7];
}
function cn(e, t, n) {
	let r = 6 * t, i = n ? r + 6 : r, a = n ? -1 : 1;
	for (let t of n ? [
		4,
		2,
		0
	] : [
		2,
		4,
		6
	]) {
		let n = a * (e[r + t] - e[i]), o = a * (e[r + t + 1] - e[i + 1]);
		if (n * n + o * o > 1e-18) return [n, o];
	}
	return null;
}
function ln(e, t = tn) {
	let n = e.pts, r = (n.length / 2 - 1) / 3, i = [];
	for (let e = 0; e < r; e++) on(n, e) > 1e-9 && i.push(e);
	if (i.length === 0) return [];
	let a = /* @__PURE__ */ new Set(), o = (e, r) => {
		let i = cn(n, e, !0), o = cn(n, r, !1);
		!i || !o || Math.abs(Math.atan2(i[0] * o[1] - i[1] * o[0], i[0] * o[0] + i[1] * o[1])) > t && a.add(r);
	};
	for (let e = 0; e + 1 < i.length; e++) o(i[e], i[e + 1]);
	return e.closed && i.length > 1 && o(i[i.length - 1], i[0]), [...a].sort((e, t) => e - t);
}
function un(e, t, n, r) {
	if (n <= 0) return 0;
	if (n >= r) return 1;
	let i = 0, a = 1, o = n / r;
	for (let s = 0; s < 12; s++) {
		let s = on(e, t, o) - n;
		if (Math.abs(s) < 1e-10 * r + 1e-14) break;
		s > 0 ? a = o : i = o;
		let c = an(e, t, o), l = c > 1e-12 ? o - s / c : (i + a) / 2;
		l > i && l < a || (l = (i + a) / 2), o = l;
	}
	return o;
}
function dn(e, t = 64, n = tn) {
	let r = e.pts, i = (r.length / 2 - 1) / 3, a = new Float64Array(2 * t), o = () => {
		for (let e = 0; e < t; e++) a[2 * e] = r[0], a[2 * e + 1] = r[1];
		return a;
	};
	if (i < 1) return o();
	let s = Array(i), c = 0;
	for (let e = 0; e < i; e++) s[e] = on(r, e), c += s[e];
	if (c < 1e-12) return o();
	let l = ln(e, n), u = e.closed ? l.length > 0 ? l : [0] : [.../* @__PURE__ */ new Set([
		0,
		...l,
		i
	])].sort((e, t) => e - t), d = [];
	if (e.closed) for (let e = 0; e < u.length; e++) {
		let t = u[e], n = e + 1 < u.length ? u[e + 1] : u[0] + i;
		d.push([t, n]);
	}
	else for (let e = 0; e + 1 < u.length; e++) d.push([u[e], u[e + 1]]);
	let f = d.map(([e, t]) => {
		let n = 0;
		for (let r = e; r < t; r++) n += s[r % i];
		return n;
	}), p = e.closed ? t : t - 1;
	if (d.length > p) throw Error(`morphicons: N=${t} too small (${d.length} runs)`);
	let m = f.reduce((e, t) => e + t, 0) || 1, h = f.map((e) => p * e / m), g = h.map((e) => Math.max(1, Math.floor(e))), _ = p - g.reduce((e, t) => e + t, 0);
	if (_ > 0) {
		let e = h.map((e, t) => [Math.round((e - Math.floor(e)) * 1e9), t]).sort((e, t) => t[0] - e[0] || e[1] - t[1]);
		for (let t = 0; t < _; t++) g[e[t % g.length][1]]++;
	}
	for (; _ < 0;) {
		let e = 0;
		for (let t = 1; t < g.length; t++) g[t] > g[e] && (e = t);
		if (g[e] <= 1) break;
		g[e]--, _++;
	}
	let v = 0;
	for (let e = 0; e < d.length; e++) {
		let [t, n] = d[e], o = g[e], c = f[e], l = t % i * 6;
		a[2 * v] = r[l], a[2 * v + 1] = r[l + 1], v++;
		let u = t, p = 0;
		for (let e = 1; e < o; e++) {
			let t = c * e / o;
			for (; u < n - 1 && p + s[u % i] < t;) p += s[u % i], u++;
			let l = u % i, d = s[l];
			sn(r, l, d > 1e-12 ? un(r, l, t - p, d) : 0, a, 2 * v), v++;
		}
	}
	if (!e.closed) {
		let e = 6 * i;
		a[2 * v] = r[e], a[2 * v + 1] = r[e + 1];
	}
	return a;
}
function fn(e, t = 64) {
	return en(e).map((e) => ({
		pts: dn(e, t),
		closed: e.closed
	}));
}
//#endregion
//#region src/vendor/morphicons/core/spring.ts
var pn = class {
	x = 1;
	v = 0;
	k = 250;
	c = 24;
	config(e, t) {
		this.k = e, this.c = t;
	}
	start() {
		this.x = 0, this.v > 14 && (this.v = 14), this.v < -14 && (this.v = -14);
	}
	step(e) {
		let t = Math.max(1, Math.min(16, Math.ceil(e / (1 / 240)))), n = e / t;
		for (let e = 0; e < t; e++) {
			let e = this.k * (1 - this.x) - this.c * this.v;
			this.v += e * n, this.x += this.v * n;
		}
		return Math.abs(1 - this.x) < .001 && Math.abs(this.v) < .02;
	}
}, mn = {
	smooth: {
		k: 170,
		c: 26
	},
	snappy: {
		k: 420,
		c: 30
	},
	bouncy: {
		k: 300,
		c: 14
	}
}, hn = /* @__PURE__ */ new Set(), $ = 0, gn = -1;
function _n(e) {
	let t = gn < 0 ? 0 : Math.min(Math.max((e - gn) / 1e3, 0), .1);
	gn = e;
	for (let e of [...hn]) e(t);
	hn.size > 0 ? $ = requestAnimationFrame(_n) : ($ = 0, gn = -1);
}
function vn(e) {
	hn.add(e), $ === 0 && (gn = -1, $ = requestAnimationFrame(_n));
}
function yn(e) {
	hn.delete(e), hn.size === 0 && $ !== 0 && (cancelAnimationFrame($), $ = 0, gn = -1);
}
var bn = /* @__PURE__ */ new WeakMap(), xn = /* @__PURE__ */ new WeakMap(), Sn = /* @__PURE__ */ new WeakMap();
function Cn(e) {
	if (typeof e == "string") return fn(e);
	let t = bn.get(e);
	return t || (t = fn(e), bn.set(e, t)), t;
}
function wn(e) {
	if (typeof e == "string") return e;
	let t = xn.get(e);
	return t || (t = Gt(en(e)), xn.set(e, t)), t;
}
function Tn(e, t) {
	if (typeof e == "string" || typeof t == "string") return Bt(Cn(e), Cn(t));
	let n = Sn.get(e);
	n || (n = /* @__PURE__ */ new WeakMap(), Sn.set(e, n));
	let r = n.get(t);
	return r || (r = Bt(Cn(e), Cn(t)), n.set(t, r)), r;
}
function En(e) {
	if (typeof e == "string") return mn[e];
	let t = mn.snappy;
	return {
		k: e?.stiffness ?? t.k,
		c: e?.damping ?? t.c
	};
}
function Dn(e, t, n) {
	let r = new pn(), i = n?.reducedMotion ?? "never", a = t, o = !0, s = null, c = null, l = null, u = 1, d = !1, f = !1;
	e.setAttribute("d", wn(t));
	let p = (t) => {
		let n = s, r = c, i = l;
		!n || !r || !i || (u = t, wt(n, t, r), e.setAttribute("d", Wt(r, i)));
	}, m = () => {
		d && (d = !1, yn(h));
	}, h = (e) => {
		let t = r.step(e);
		p(r.x), t && (m(), g());
	}, g = () => {
		o = !0, s = null, c = null, l = null, u = 1, r.x = 1, r.v = 0, e.setAttribute("d", wn(a));
	}, _ = () => {
		let e = s, t = c;
		return o || !e || !t ? Cn(a) : t.map((t, n) => ({
			pts: Float64Array.from(t),
			closed: e.items[n].closed
		}));
	}, v = (e) => {
		s = o ? Tn(a, e) : Bt(_(), Cn(e)), c = Ct(s), l = s.items.map((e) => e.closed), a = e, o = !1;
	}, y = (e) => {
		m(), a = e, g();
	}, b = () => i === "always" ? !0 : i !== "user" || typeof matchMedia > "u" ? !1 : matchMedia?.("(prefers-reduced-motion: reduce)").matches ?? !1, x = (e, t) => {
		if (f) return;
		let n = !o && s !== null && e === a;
		m(), r.v = 0, n || v(e), p(t);
	};
	return {
		morphTo(e, t) {
			if (f || e === a && (o || d)) return;
			if (b()) {
				y(e);
				return;
			}
			let { k: n, c: i } = En(t);
			r.config(n, i), v(e), r.start(), d || (d = !0, vn(h));
		},
		set(e) {
			f || y(e);
		},
		seek: x,
		get progress() {
			return o ? 1 : u;
		},
		set progress(e) {
			f || x(a, e);
		},
		get reducedMotion() {
			return i;
		},
		set reducedMotion(e) {
			i = e;
		},
		destroy() {
			m(), f = !0, s = null, c = null, l = null;
		}
	};
}
//#endregion
//#region src/vendor/morphicons/react/index.tsx
var On = typeof document > "u" ? i : s;
function kn(e, t, n) {
	if (n <= 0) return wn(e);
	if (n >= 1) return wn(t);
	let r = Bt(fn(e), fn(t)), i = Ct(r);
	return wt(r, n, i), Wt(i, r.items.map((e) => e.closed));
}
var An = t(function(e, t) {
	let { icon: r, from: a, to: s, progress: u, spring: d, reducedMotion: f, size: p = 24, color: m = "currentColor", strokeWidth: h = 2, absoluteStrokeWidth: g, label: _, ...v } = e, y = a !== void 0 && s !== void 0, b = r ?? a ?? s, [x] = l(() => y ? kn(a, s, u ?? 0) : b === void 0 ? "" : wn(b)), S = c(null), C = c(null), w = c(d);
	w.current = d;
	let T = c(f);
	T.current = f;
	let E = c(r), D = c(y), O = c(!1), k = c(!1), A = c(null), j = n((e) => {
		if (C.current) return C.current;
		let t = S.current;
		return O.current || !t ? null : (C.current = Dn(t, e, { reducedMotion: T.current }), C.current);
	}, []);
	On(() => {
		O.current = !1;
		let e = S.current;
		if (e && b !== void 0) {
			let t = Dn(e, y ? a : b, { reducedMotion: T.current });
			if (C.current = t, y) {
				A.current = [a, s];
				let e = u ?? 0;
				e <= 0 ? t.set(a) : e >= 1 ? t.set(s) : (t.seek(s, e), k.current = !0);
			}
		}
		return () => {
			O.current = !0, C.current?.destroy(), C.current = null, k.current = !1, A.current = null;
		};
	}, []), i(() => {
		let e = C.current;
		e && (e.reducedMotion = f ?? "never");
	}, [f]), i(() => {
		let e = D.current && !y;
		D.current = y;
		let t = r !== E.current;
		if (E.current = r, y || r === void 0 || !t && !e) return;
		A.current = null, k.current = !1;
		let n = C.current;
		n ? n.morphTo(r, w.current) : j(r);
	}, [
		r,
		y,
		j
	]), i(() => {
		if (!y) return;
		let e = C.current ?? j(a);
		if (!e) return;
		let t = u ?? 0;
		(!A.current || A.current[0] !== a || A.current[1] !== s) && (A.current = [a, s], k.current = !1), t <= 0 ? (e.set(a), k.current = !1) : t >= 1 ? (e.set(s), k.current = !1) : (k.current ||= (e.set(a), !0), e.seek(s, t));
	}, [
		y,
		a,
		s,
		u,
		j
	]), o(t, () => ({
		morphTo: (e, t) => {
			A.current = null, k.current = !1;
			let n = C.current;
			n ? n.morphTo(e, t ?? w.current) : j(e);
		},
		set: (e) => {
			A.current = null, k.current = !1;
			let t = C.current;
			t ? t.set(e) : j(e);
		}
	}), [j]);
	let M = g ? Number(h) * 24 / Number(p) : h;
	return /* @__PURE__ */ (0, Y.jsxs)("svg", {
		xmlns: "http://www.w3.org/2000/svg",
		width: p,
		height: p,
		viewBox: "0 0 24 24",
		fill: "none",
		stroke: m,
		strokeWidth: M,
		strokeLinecap: "round",
		strokeLinejoin: "round",
		role: _ ? "img" : void 0,
		"aria-hidden": !_ || void 0,
		...v,
		children: [_ ? /* @__PURE__ */ (0, Y.jsx)("title", { children: _ }) : null, /* @__PURE__ */ (0, Y.jsx)("path", {
			ref: S,
			d: x
		})]
	});
});
//#endregion
//#region src/components/MorphIcon.tsx
function jn(e) {
	return /* @__PURE__ */ (0, Y.jsx)(An, {
		reducedMotion: "user",
		...e
	});
}
var Mn = {
	menu: "M4 6h16M4 12h16M4 18h16",
	close: "M6 6l12 12M18 6L6 18",
	play: "M8 5l11 7-11 7z",
	pause: "M9 5v14M15 5v14",
	plus: "M12 5v14M5 12h14",
	check: "M5 12l4 4L19 6",
	arrowRight: "M5 12h14M13 6l6 6-6 6",
	arrowLeft: "M19 12H5M11 6l-6 6 6 6",
	search: "M11 4a7 7 0 1 0 0 14 7 7 0 0 0 0-14M16 16l4 4"
};
//#endregion
export { gt as Accordion, _t as BlurReveal, at as BrandLogo, rt as BrandProvider, ot as BrandThinkingLogo, ut as Button, xt as ColorSelector, vt as FadeUp, St as FluidDotOrbit, dt as IconButton, ft as LoadingButton, bt as MagneticButton, jn as MorphingIcon, pt as SegmentedControl, mt as SliderDetents, lt as Surface, et as ThinkingLogo, yt as TiltCard, ht as Toggle, tt as defaultBrand, ct as hoverLiftMotion, Mn as morphIconShapes, X as motionTokens, st as pressMotion, it as useBrand };
