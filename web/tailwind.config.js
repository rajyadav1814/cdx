/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: {
          base:     'var(--bg-base)',
          surface:  'var(--bg-surface)',
          surface2: 'var(--bg-surface2)',
          surface3: 'var(--bg-surface3)',
          input:    'var(--bg-input)',
        },
        brand: {
          red:      '#CC1B1B',
          'red-lt': '#E83030',
          'red-dim':'rgba(204,27,27,0.12)',
          gold:     '#D4A017',
          'gold-dim':'rgba(212,160,23,0.10)',
          blue:     '#2563EB',
        },
        agent: {
          green:  '#1D9E75',
          purple: '#8B7FE8',
          blue:   '#4A9EE8',
          amber:  '#D4924A',
        },
        provider: {
          anthropic: '#D4845A',
          openai:    '#19C37D',
        },
        text: {
          primary:   'var(--text-primary)',
          secondary: 'var(--text-secondary)',
          muted:     'var(--text-muted)',
          accent:    'var(--text-accent)',
        },
      },
      fontFamily: {
        display: ['Satoshi', 'system-ui', 'sans-serif'],
        sans:    ['DM Sans', 'system-ui', 'sans-serif'],
        mono:    ['JetBrains Mono', 'monospace'],
      },
      fontSize: {
        'display': ['64px', { lineHeight:'1.0',  letterSpacing:'-0.04em', fontWeight:'900' }],
        'hero':    ['48px', { lineHeight:'1.05', letterSpacing:'-0.03em', fontWeight:'700' }],
        'title':   ['32px', { lineHeight:'1.1',  letterSpacing:'-0.02em', fontWeight:'700' }],
        'heading': ['20px', { lineHeight:'1.2',  letterSpacing:'-0.01em', fontWeight:'700' }],
        'kpi':     ['36px', { lineHeight:'1',    letterSpacing:'-0.02em', fontWeight:'700' }],
        'label':   ['11px', { lineHeight:'1',    letterSpacing:'0.08em',  fontWeight:'500' }],
      },
      borderRadius: {
        DEFAULT: '2px', sm:'2px', md:'2px', lg:'4px', full:'9999px',
      },
      animation: {
        'fade-in':  'fadeIn 0.2s ease-out',
        'slide-up': 'slideUp 0.25s ease-out',
        'pulse-dot':'pulseDot 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn:   { from:{opacity:0}, to:{opacity:1} },
        slideUp:  { from:{opacity:0,transform:'translateY(8px)'}, to:{opacity:1,transform:'translateY(0)'} },
        pulseDot: { '0%,100%':{opacity:1}, '50%':{opacity:0.3} },
      },
    },
  },
  plugins: [require("@tailwindcss/typography")],
}
