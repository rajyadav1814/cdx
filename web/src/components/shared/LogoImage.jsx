// Place chromadata-logo.svg in ~/cdx/web/public/brand/
// Until then "CD" + "Chromadata" text fallback renders automatically.

import { useState } from 'react'
import LogoIcon from './LogoIcon'
import { cn } from '@/lib/utils'

const HEIGHTS = { sm: 'h-6', md: 'h-8', lg: 'h-12' }

export default function LogoImage({ size = 'md', className = '' }) {
  const [useFallback, setUseFallback] = useState(false)
  const height = HEIGHTS[size] || HEIGHTS.md

  if (useFallback) {
    return (
      <div className={cn('flex items-center gap-2.5', className)}>
        <LogoIcon size={size} />
        <span
          className="font-display font-bold text-text-primary tracking-tight"
          style={{ fontSize: size === 'lg' ? 22 : size === 'sm' ? 14 : 17 }}
        >
          Chromadata
        </span>
      </div>
    )
  }

  return (
    <img
      src="/brand/chromadata-logo.svg"
      alt="Chromadata"
      className={cn(height, 'w-auto object-contain', className)}
      onError={() => setUseFallback(true)}
    />
  )
}
