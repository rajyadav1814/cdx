const SIZES = { sm: 20, md: 28, lg: 40 }

export default function AgentBadge({ id, color, size = 'sm' }) {
  const px = SIZES[size] || SIZES.sm
  const fontSize = size === 'lg' ? 14 : size === 'md' ? 11 : 9

  return (
    <div
      className="flex items-center justify-center flex-shrink-0 font-mono font-bold"
      style={{
        width: px,
        height: px,
        borderRadius: 2,
        backgroundColor: `${color}26`,   // 15% opacity
        borderTop: `2px solid ${color}B3`, // 70% opacity
        color,
        fontSize,
      }}
    >
      {String(id).padStart(2, '0')}
    </div>
  )
}
