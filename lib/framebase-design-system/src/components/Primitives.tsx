import { useId, useState, type ButtonHTMLAttributes, type ReactNode } from "react";
import { AnimatePresence, motion } from "motion/react";
import { BrandThinkingLogo } from "./Brand";
import { motionTokens, pressMotion } from "../motion/presets";

export function Surface({ children, className = "" }: { children: ReactNode; className?: string }) { return <section className={`lf-surface ${className}`}>{children}</section>; }

export function Button({ variant = "primary", size = "md", className = "", children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary"|"secondary"|"ghost"; size?: "sm"|"md"|"lg" }) {
  return <motion.button whileTap={props.disabled ? undefined : pressMotion} className={`lf-button lf-button--${variant} lf-button--${size} ${className}`} {...props}>{children}</motion.button>;
}

export function IconButton({ label, children, className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { label: string }) {
  return <motion.button type="button" whileTap={pressMotion} className={`lf-icon-button ${className}`} aria-label={label} {...props}>{children}</motion.button>;
}

export type LoadingState = "idle"|"pending"|"success"|"error";
export function LoadingButton({ state = "idle", idleLabel = "Продолжить", pendingLabel = "Собираем…", successLabel = "Готово", errorLabel = "Повторить", children, ...props }: ButtonHTMLAttributes<HTMLButtonElement> & { state?: LoadingState; idleLabel?: string; pendingLabel?: string; successLabel?: string; errorLabel?: string }) {
  const face = state === "pending" ? <><BrandThinkingLogo state="working" size={20}/>{pendingLabel}</> : state === "success" ? <>✓ {successLabel}</> : state === "error" ? <>↻ {errorLabel}</> : children ?? idleLabel;
  return <Button disabled={state === "pending" || props.disabled} {...props}><AnimatePresence mode="wait" initial={false}><motion.span className="lf-button-face" key={state} initial={{ opacity: 0, y: 5, filter: "blur(4px)" }} animate={{ opacity: 1, y: 0, filter: "blur(0px)" }} exit={{ opacity: 0, y: -5, filter: "blur(4px)" }} transition={{ duration: motionTokens.fast }}>{face}</motion.span></AnimatePresence></Button>;
}

export function SegmentedControl<T extends string>({ items, value, onChange, label = "Выбор" }: { items: ReadonlyArray<{ value: T; label: string }>; value: T; onChange: (value:T)=>void; label?: string }) {
  const active = Math.max(0, items.findIndex(i => i.value === value));
  return <div className="lf-segmented" role="radiogroup" aria-label={label} style={{ gridTemplateColumns: `repeat(${items.length},1fr)` }}>
    <motion.span className="lf-segment-pill" aria-hidden style={{ width: `calc((100% - 6px) / ${items.length})` }} animate={{ x: `${active * 100}%` }} transition={motionTokens.spring}/>
    {items.map(item => <button className="lf-segment" role="radio" aria-checked={item.value === value} key={item.value} onClick={() => onChange(item.value)}>{item.label}</button>)}
  </div>;
}

export function SliderDetents({ value, min = 0, max = 100, step = 1, detents = [], onChange, label = "Значение" }: { value:number; min?:number; max?:number; step?:number; detents?:number[]; onChange:(value:number)=>void; label?:string }) {
  const id = useId();
  return <div className="lf-slider"><label htmlFor={id}>{label}</label><input id={id} type="range" min={min} max={max} step={step} value={value} onChange={e => onChange(Number(e.target.value))}/>{detents.length > 0 && <div className="lf-detents">{detents.map(v => <span key={v}>{v}</span>)}</div>}</div>;
}

export function Toggle({ checked, onChange, label }: { checked:boolean; onChange:(value:boolean)=>void; label:string }) {
  return <button type="button" role="switch" aria-checked={checked} aria-label={label} className="lf-toggle" data-on={checked} onClick={() => onChange(!checked)}><motion.span className="lf-toggle-knob" animate={{ x: checked ? 18 : 0 }} transition={motionTokens.springSnappy}/></button>;
}

export function Accordion({ title, children, defaultOpen = false }: { title:string; children:ReactNode; defaultOpen?:boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return <div><button className="lf-button lf-button--ghost" aria-expanded={open} onClick={() => setOpen(v => !v)}>{title}<motion.span animate={{ rotate: open ? 180 : 0 }}>⌄</motion.span></button><AnimatePresence initial={false}>{open && <motion.div initial={{ height:0, opacity:0 }} animate={{ height:"auto", opacity:1 }} exit={{ height:0, opacity:0 }} transition={{ duration:motionTokens.base, ease:motionTokens.easeOut }} style={{ overflow:"hidden" }}>{children}</motion.div>}</AnimatePresence></div>;
}
