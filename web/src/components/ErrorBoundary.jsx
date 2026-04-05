import React from 'react'
import { AlertTriangle } from 'lucide-react'

export default class ErrorBoundary extends React.Component {
  state = { hasError: false, error: null }

  static getDerivedStateFromError(error) {
    return { hasError: true, error }
  }

  componentDidCatch(error, info) {
    console.error('[CDX] Panel render error:', error, info)
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="h-full flex items-center justify-center p-8">
          <div
            className="card max-w-md w-full"
            style={{ borderColor: 'rgba(204,27,27,0.5)' }}
          >
            <div className="flex items-center gap-2 mb-3">
              <AlertTriangle size={18} className="text-brand-red flex-shrink-0" />
              <span className="font-display font-bold text-heading text-text-primary">
                Panel Error
              </span>
            </div>
            <p className="text-text-secondary text-sm mb-4">
              Something went wrong rendering this panel.
            </p>
            <details className="mb-4">
              <summary className="label text-text-muted cursor-pointer hover:text-text-secondary transition-colors">
                Error details
              </summary>
              <pre className="text-xs text-text-muted mt-2 font-mono overflow-auto whitespace-pre-wrap break-words">
                {this.state.error?.message}
              </pre>
            </details>
            <button
              className="btn-ghost text-sm"
              onClick={() => this.setState({ hasError: false, error: null })}
            >
              Retry panel
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}
