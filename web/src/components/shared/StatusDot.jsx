const STATUS = {
  fresh: '#1D9E75',
  stale: '#D4924A',
  idle:  '#4A4A5E',
}

export default function StatusDot({ status = 'idle' }) {
  const color = STATUS[status] || STATUS.idle
  const pulse = status === 'fresh'

  return (
    <span
      className={pulse ? 'animate-pulse-dot' : ''}
      style={{
        display: 'inline-block',
        width: 6,
        height: 6,
        borderRadius: '50%',
        backgroundColor: color,
        flexShrink: 0,
      }}
    />
  )
}
