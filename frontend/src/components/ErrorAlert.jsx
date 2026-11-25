export default function ErrorAlert({ message, onDismiss }) {
  return (
    <div className="error-alert">
      <div className="error-content">
        <span className="error-icon">⚠️</span>
        <div className="error-text">
          <strong>Error</strong>
          <p>{message}</p>
        </div>
      </div>
      {onDismiss && (
        <button className="btn-close" onClick={onDismiss}>✕</button>
      )}
    </div>
  )
}
