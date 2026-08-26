"use client"

import { motion, useMotionValue, useReducedMotion, useSpring, useTransform } from "motion/react"
import { useRef, type ButtonHTMLAttributes, type ReactNode } from "react"

// Adapted from Spell UI's BlurReveal and Amicro's FadeUp, TiltCard and MagneticButton.
export function BlurReveal({ children, className = "" }: { children: string; className?: string }) {
  const reduced = useReducedMotion()
  return <span className={className} aria-label={children}>{children.split("").map((char, index) => <motion.span aria-hidden="true" className="reveal-char" key={`${char}-${index}`} initial={reduced ? false : { opacity: 0, filter: "blur(8px)", y: 7 }} animate={{ opacity: 1, filter: "blur(0px)", y: 0 }} transition={reduced ? { duration: 0 } : { delay: index * 0.018, duration: 0.3 }}>{char === " " ? "\u00a0" : char}</motion.span>)}</span>
}

export function FadeUp({ children, delay = 0, className = "" }: { children: ReactNode; delay?: number; className?: string }) {
  const reduced = useReducedMotion()
  return <motion.div className={className} initial={reduced ? false : { opacity: 0, y: 14 }} animate={{ opacity: 1, y: 0 }} transition={reduced ? { duration: 0 } : { duration: 0.45, delay, ease: [0.16, 1, 0.3, 1] }}>{children}</motion.div>
}

export function TiltCard({ children, active, onClick }: { children: ReactNode; active: boolean; onClick: () => void }) {
  const ref = useRef<HTMLButtonElement>(null)
  const reduced = useReducedMotion()
  const x = useMotionValue(0)
  const y = useMotionValue(0)
  const rotateX = useSpring(useTransform(y, [-0.5, 0.5], [4, -4]), { stiffness: 220, damping: 25 })
  const rotateY = useSpring(useTransform(x, [-0.5, 0.5], [-4, 4]), { stiffness: 220, damping: 25 })
  return <motion.button ref={ref} type="button" className={`template-card ${active ? "is-active" : ""}`} style={reduced ? undefined : { rotateX, rotateY, transformPerspective: 800 }} onPointerMove={event => { if (reduced || !ref.current) return; const rect = ref.current.getBoundingClientRect(); x.set((event.clientX - rect.left) / rect.width - 0.5); y.set((event.clientY - rect.top) / rect.height - 0.5) }} onPointerLeave={() => { x.set(0); y.set(0) }} onClick={onClick} aria-pressed={active}>{children}</motion.button>
}

export function MagneticButton({ children, className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  const ref = useRef<HTMLButtonElement>(null)
  const reduced = useReducedMotion()
  const x = useSpring(0, { stiffness: 180, damping: 18 })
  const y = useSpring(0, { stiffness: 180, damping: 18 })
  return <motion.button {...props} ref={ref} className={className} style={reduced ? undefined : { x, y }} onPointerMove={event => { if (reduced || !ref.current) return; const rect = ref.current.getBoundingClientRect(); x.set((event.clientX - rect.left - rect.width / 2) * 0.13); y.set((event.clientY - rect.top - rect.height / 2) * 0.13) }} onPointerLeave={() => { x.set(0); y.set(0) }}>{children}</motion.button>
}

// Adapted from Spell UI's ColorSelector, expressed as a controlled, accessible group.
export function ColorSelector<T extends string>({ items, value, onChange }: { items: ReadonlyArray<{ id: T; name: string; colors: readonly [string, string] }>; value: T; onChange: (value: T) => void }) {
  return <div className="background-swatches" role="radiogroup" aria-label="Background palette">{items.map(item => <motion.button key={item.id} type="button" role="radio" aria-label={item.name} aria-checked={item.id === value} className={item.id === value ? "active" : ""} style={{ background: `linear-gradient(145deg,${item.colors[0]},${item.colors[1]})` }} whileTap={{ scale: 0.9 }} onClick={() => onChange(item.id)}/>)}</div>
}

// Adapted from Amicro's FluidDotOrbit.
export function FluidDotOrbit() {
  const reduced = useReducedMotion()
  return <span className="fluid-orbit" aria-hidden="true"><i/><motion.b animate={reduced ? undefined : { rotate: 360 }} transition={{ duration: 1.8, repeat: Infinity, ease: "linear" }}><i/></motion.b></span>
}
