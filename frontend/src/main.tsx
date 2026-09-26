import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { LazyMotion, MotionConfig } from 'motion/react'
import './index.css'
import App from './App'

const root = document.getElementById('root')
if (!root) throw new Error('Application root is missing.')

const loadMotionFeatures = () => import('./motionFeatures').then((module) => module.default)

createRoot(root).render(
  <StrictMode>
    <MotionConfig reducedMotion="user">
      <LazyMotion features={loadMotionFeatures} strict>
        <App />
      </LazyMotion>
    </MotionConfig>
  </StrictMode>,
)
