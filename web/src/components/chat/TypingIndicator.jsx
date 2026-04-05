export default function TypingIndicator({ modelLabel, accentColor }) {
  return (
    <div className="flex items-start gap-2 px-4 py-3">
      {/* CD badge */}
      <div
        className="flex-shrink-0 flex items-center justify-center w-6 h-6 rounded-sm font-mono font-bold text-[9px]"
        style={{
          backgroundColor: `${accentColor}1A`,
          borderTop: `2px solid ${accentColor}B3`,
          color: accentColor,
        }}
      >
        CD
      </div>

      <div className="flex flex-col gap-1">
        <div className="flex items-center gap-1.5">
          {[0, 1, 2].map(i => (
            <span
              key={i}
              className="inline-block w-1.5 h-1.5 rounded-full animate-pulse"
              style={{
                backgroundColor: accentColor,
                animationDelay: `${i * 0.2}s`,
                animationDuration: '1s',
              }}
            />
          ))}
        </div>
        {modelLabel && (
          <span className="text-[10px] text-text-muted">
            Thinking with {modelLabel}...
          </span>
        )}
      </div>
    </div>
  )
}
