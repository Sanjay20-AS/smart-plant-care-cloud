export default function MoistureIndicator({ moisture, minThreshold = 30, maxThreshold = 80 }) {
  if (moisture === null || moisture === undefined) {
    return <span className="moisture-unknown">No data</span>
  }

  let status = 'normal'
  if (moisture < minThreshold) status = 'dry'
  else if (moisture > maxThreshold) status = 'wet'

  const percentage = Math.min(100, Math.max(0, moisture))
  const hue = status === 'dry' ? 0 : status === 'wet' ? 240 : 120

  return (
    <div className="moisture-indicator">
      <div className="moisture-bar">
        <div
          className="moisture-fill"
          style={{
            width: `${percentage}%`,
            backgroundColor: `hsl(${hue}, 100%, 50%)`,
          }}
        ></div>
      </div>
      <span className={`moisture-label moisture-${status}`}>{moisture.toFixed(1)}%</span>
    </div>
  )
}
