"use client"

import { useCallback, useEffect, useRef, useState, type ReactNode } from "react"
import { motion, useReducedMotion } from "motion/react"
import { IconAlertCircle, IconCheck } from "@tabler/icons-react"
import { ThinkingOrb } from "thinking-orbs"

const SPRING = { type: "spring" as const, stiffness: 520, damping: 34, mass: 0.45 }

type Props = { action: () => Promise<void>; children: ReactNode; disabled?: boolean; icon?: ReactNode }

export function LoadingButton({ action, children, disabled = false, icon }: Props) {
  const [status, setStatus] = useState<"idle" | "pending" | "success" | "error">("idle")
  const phase = useRef(status)
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null)
  const reduced = useReducedMotion()

  useEffect(() => () => { if (timer.current) clearTimeout(timer.current) }, [])

  const run = useCallback(async () => {
    if (phase.current === "pending" || disabled) return
    phase.current = "pending"
    setStatus("pending")
    try { await action(); phase.current = "success"; setStatus("success") }
    catch { phase.current = "error"; setStatus("error") }
    timer.current = setTimeout(() => { phase.current = "idle"; setStatus("idle") }, 1450)
  }, [action, disabled])

  const labels = { idle: children, pending: "Рендеринг", success: "Сохранено", error: "Повторить" }
  return <motion.button className="export-button" type="button" onClick={run} disabled={disabled} aria-busy={status === "pending"} whileTap={disabled || reduced ? undefined : { y: 1 }} transition={SPRING}>
    <span className="button-state-grid" aria-hidden="true">{(Object.keys(labels) as Array<keyof typeof labels>).map(face => <motion.span className={`button-face ${face}`} key={face} initial={false} animate={face === status ? { opacity: 1, y: 0, filter: "blur(0px)" } : { opacity: 0, y: 3, filter: "blur(3px)" }} transition={reduced ? { duration: 0 } : { type: "spring", stiffness: 260, damping: 34, mass: 0.8 }}>{face === "idle" ? icon : face === "pending" ? <ThinkingOrb state="working" size={20} theme="light" speed={0.9} paused={Boolean(reduced) || status !== "pending"}/> : face === "success" ? <IconCheck size={18} stroke={2}/> : <IconAlertCircle size={18} stroke={1.8}/>}<span>{labels[face]}</span></motion.span>)}</span>
    <span className="sr-only" role="status">{String(labels[status])}</span>
  </motion.button>
}
