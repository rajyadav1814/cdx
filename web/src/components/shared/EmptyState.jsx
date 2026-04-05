export default function EmptyState({ icon: Icon, title, message, action, onAction }) {
  return (
    <div className="flex flex-col items-center justify-center h-full gap-4 px-8 text-center">
      {Icon && <Icon size={32} className="text-text-muted" strokeWidth={1.5} />}
      {title && (
        <div className="font-display font-bold text-heading text-text-primary">
          {title}
        </div>
      )}
      {message && (
        <div className="text-sm text-text-secondary max-w-xs leading-relaxed">
          {message}
        </div>
      )}
      {action && (
        <button className="btn-primary mt-2" onClick={onAction}>
          {action}
        </button>
      )}
    </div>
  )
}
