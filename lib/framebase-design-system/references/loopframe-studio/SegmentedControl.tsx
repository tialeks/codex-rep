"use client"

import { motion, useReducedMotion } from "motion/react"

type Item<T extends string> = { label: string; value: T }

export function SegmentedControl<T extends string>({ items, value, onChange, label }: { items: Item<T>[]; value: T; onChange: (value: T) => void; label: string }) {
  const reduced = useReducedMotion()
  return <div className="segmented" role="radiogroup" aria-label={label}>{items.map(item => <button key={item.value} type="button" role="radio" aria-checked={item.value === value} className={item.value === value ? "active" : ""} onClick={() => onChange(item.value)}>{item.value === value && <motion.span className="segment-active" layoutId={`segment-${label}`} transition={reduced ? { duration: 0 } : { type: "spring", stiffness: 430, damping: 36 }}/>}<span>{item.label}</span></button>)}</div>
}
