import { motion, useReducedMotion } from 'motion/react'

export function SegmentedControl({ items, value, onChange, label = 'Параметры' }) {
  const reduced = useReducedMotion()
  return <div className="interior-segmented" role="radiogroup" aria-label={label}>
    {items.map(item => <button key={item.value} type="button" role="radio" aria-checked={item.value === value} className={item.value === value ? 'active' : ''} onClick={() => onChange(item.value)}>
      {item.value === value && <motion.span className="segment-active" layoutId={`segment-${label}`} transition={reduced ? { duration: 0 } : { type: 'spring', stiffness: 430, damping: 36 }}/>}<span>{item.label}</span>
    </button>)}
  </div>
}
