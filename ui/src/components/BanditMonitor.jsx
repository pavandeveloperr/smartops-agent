function BanditMonitor({ banditRows, armLabels }) {
  return (
    <aside className="monitor-panel">
      <div className="monitor-header">
        <div>
          <p className="eyebrow">Bandit monitor</p>
          <h2>Live routing view</h2>
        </div>
        <span className="monitor-pill">GET /bandit</span>
      </div>

      {!banditRows.length ? (
        <div className="empty-state compact">
          <p>No bandit snapshot yet.</p>
        </div>
      ) : (
        <div className="bandit-table">
          <div className="bandit-header-row">
            <span>State</span>
            {armLabels.map((label) => (
              <span key={label}>{label}</span>
            ))}
          </div>
          {banditRows.map((row) => (
            <div className="bandit-row" key={row.state}>
              <span className="state-label">{row.state}</span>
              {row.arms.map((arm) => (
                <span key={`${row.state}-${arm.label}`} className="bandit-cell">
                  <strong>{arm.value.q.toFixed(2)}</strong>
                  <small>n={arm.value.n}</small>
                </span>
              ))}
            </div>
          ))}
        </div>
      )}
    </aside>
  )
}

export default BanditMonitor
