export default function StatusBadge({ status, type = 'status' }) {
  let className = 'badge'
  
  if (type === 'alert') {
    className += ` badge-${status?.toLowerCase() || 'info'}`
  } else if (type === 'device') {
    className += ` badge-${status?.toLowerCase() || 'inactive'}`
  } else {
    className += ` badge-${status ? 'active' : 'inactive'}`
  }
  
  const displayStatus = typeof status === 'boolean' 
    ? (status ? 'Active' : 'Inactive')
    : (status || 'Unknown')
  
  return <span className={className}>{displayStatus}</span>
}
