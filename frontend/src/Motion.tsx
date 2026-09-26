import { useReducedMotion, type Variants } from 'motion/react'
import * as m from 'motion/react-m'
import type { ReactNode } from 'react'

const revealGroup: Variants = {
  hidden: { opacity: 0, y: 16 },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.36,
      ease: [0.22, 1, 0.36, 1],
      staggerChildren: 0.1,
    },
  },
}

const revealItem: Variants = {
  hidden: { opacity: 0, y: 10 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.3, ease: [0.22, 1, 0.36, 1] },
  },
}

interface RevealProps {
  children: ReactNode
  className?: string
  labelledBy?: string
}

export function RevealSection({ children, className, labelledBy }: RevealProps) {
  const reduceMotion = useReducedMotion()
  return (
    <m.section
      aria-labelledby={labelledBy}
      className={className}
      data-motion-reveal="once"
      initial={reduceMotion ? false : 'hidden'}
      whileInView="visible"
      viewport={{ once: true, amount: 0.18 }}
      variants={revealGroup}
    >
      {children}
    </m.section>
  )
}

export function RevealItem({ children, className }: Omit<RevealProps, 'labelledBy'>) {
  return <m.div className={className} variants={revealItem}>{children}</m.div>
}
