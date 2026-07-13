import { useState, useEffect } from 'react'
import { Sun, Moon } from 'lucide-react'
import LogoImage from '@/components/shared/LogoImage'

export default function Header() {
  const [isDark, setIsDark] = useState(true)

  useEffect(() => {
    // Check initial state from HTML class
    const isDarkMode = document.documentElement.classList.contains('dark')
    setIsDark(isDarkMode)
  }, [])

  const toggleTheme = () => {
    const root = document.documentElement
    if (isDark) {
      root.classList.remove('dark')
      setIsDark(false)
    } else {
      root.classList.add('dark')
      setIsDark(true)
    }
  }

  return (
    <header
      className="sticky top-0 z-50 flex items-center justify-between px-6 bg-bg-base border-b"
      style={{
        height: 56,
        borderColor: 'var(--border-color)',
      }}
    >
      <LogoImage size="md" />

      <div className="flex items-center gap-4">
        <button
          onClick={toggleTheme}
          className="btn-icon"
          title="Toggle Theme"
        >
          {isDark ? <Sun size={18} /> : <Moon size={18} />}
        </button>

        <div
          style={{
            width: 1,
            height: 16,
            backgroundColor: 'var(--border-color)',
          }}
        />
        <div>
          <div className="label text-text-muted">Presented to</div>
          <div
            className="font-display font-bold text-brand-gold"
            style={{ fontSize: 14, letterSpacing: '-0.01em' }}
          >
            Sony Music Latin
          </div>
        </div>
      </div>
    </header>
  )
}
