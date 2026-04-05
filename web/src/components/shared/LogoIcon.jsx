// Place chromadata-icon.svg in ~/cdx/web/public/brand/
// Until then "CD" text placeholder renders automatically.

import { useState } from 'react'

const SIZES = { sm: 22, md: 28, lg: 40 }

export default function LogoIcon({ size = 'md' }) {
  const [useFallback, setUseFallback] = useState(false)
  const px = SIZES[size] || SIZES.md

  if (useFallback) {
    return (
      <div
        className="bg-brand-blue flex items-center justify-center flex-shrink-0"
        style={{ width: px, height: px, borderRadius: 2 }}
      >
        <span
          className="font-display font-black text-white"
          style={{ fontSize: px * 0.38 }}
        >
          CD
        </span>
      </div>
    )
  }

  return (
    <img
      src="/brand/chromadata-icon.svg"
      alt=""
      style={{ width: px, height: px }}
      className="object-contain flex-shrink-0"
      onError={() => setUseFallback(true)}
    />
  )
}
