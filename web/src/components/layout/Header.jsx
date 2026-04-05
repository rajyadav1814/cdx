import LogoImage from '@/components/shared/LogoImage'

export default function Header() {
  return (
    <header
      className="sticky top-0 z-50 flex items-center justify-between px-6"
      style={{
        height: 56,
        backgroundColor: '#05050A',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
      }}
    >
      <LogoImage size="md" />

      <div className="flex items-center gap-4">
        <div
          style={{
            width: 1,
            height: 16,
            backgroundColor: 'rgba(255,255,255,0.10)',
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
