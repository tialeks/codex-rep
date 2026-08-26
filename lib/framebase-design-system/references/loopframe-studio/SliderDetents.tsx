"use client"

export function SliderDetents({ label, value, min, max, step = 1, unit = "", detents = [], onChange }: { label: string; value: number; min: number; max: number; step?: number; unit?: string; detents?: number[]; onChange: (value: number) => void }) {
  const progress = ((value - min) / (max - min)) * 100
  return <label className="interior-slider"><span className="slider-label"><span>{label}</span><output>{Number.isInteger(value) ? value : value.toFixed(1)}{unit}</output></span><span className="slider-track"><i style={{ width: `${progress}%` }}/>{detents.map(detent => <b key={detent} style={{ left: `${((detent - min) / (max - min)) * 100}%` }}/>)}</span><input type="range" min={min} max={max} step={step} value={value} onChange={event => onChange(Number(event.target.value))}/></label>
}
