import { useCallback, useEffect, useRef, useState } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { IconAlertCircle, IconCircleCheck } from '@tabler/icons-react'
import { ThinkingOrb } from 'thinking-orbs'

const SPRING = { type: 'spring', stiffness: 520, damping: 34, mass: .45 }

export function LoadingButton({ action, children, pendingLabel = 'Рендеринг', successLabel = 'Сохранено', className = '', disabled = false, icon }) {
  const [status, setStatus] = useState('idle')
  const phase = useRef('idle')
  const timer = useRef(null)
  const reduced = useReducedMotion()

  useEffect(() => () => clearTimeout(timer.current), [])
  const run = useCallback(async () => {
    if (phase.current === 'pending' || disabled) return
    phase.current = 'pending'; setStatus('pending')
    try { await Promise.all([action(), new Promise(resolve => setTimeout(resolve, 900))]); phase.current = 'success'; setStatus('success') }
    catch { phase.current = 'error'; setStatus('error') }
    timer.current = setTimeout(() => { phase.current = 'idle'; setStatus('idle') }, 1450)
  }, [action, disabled])

  const label = status === 'pending' ? pendingLabel : status === 'success' ? successLabel : status === 'error' ? 'Повторить' : children
  return <motion.button type="button" className={`interior-button ${className}`} onClick={run} disabled={disabled} aria-busy={status === 'pending'} whileTap={disabled || reduced ? undefined : { y: 1 }} transition={SPRING}>
    <span className="interior-button-grid" aria-hidden="true">
      {['idle', 'pending', 'success', 'error'].map(face => <motion.span key={face} className={`interior-button-face ${face}`} initial={false} animate={face === status ? { opacity: 1, y: 0, filter: 'blur(0px)' } : { opacity: 0, y: 3, filter: 'blur(3px)' }} transition={reduced ? { duration: 0 } : { type: 'spring', stiffness: 260, damping: 34, mass: .8 }}>
        {face === 'idle' ? icon : face === 'pending' ? <ThinkingOrb className="thinking-orb" state="working" size={20} theme="light" aria-label="Рендеринг"/> : face === 'success' ? <IconCircleCheck size={17} stroke={1.8}/> : <IconAlertCircle size={17} stroke={1.8}/>}
        <span>{face === 'idle' ? children : face === 'pending' ? pendingLabel : face === 'success' ? successLabel : 'Повторить'}</span>
      </motion.span>)}
    </span>
    <span className="sr-only" role="status">{label}</span>
  </motion.button>
}
