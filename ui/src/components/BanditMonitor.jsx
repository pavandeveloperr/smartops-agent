import { useState } from "react";
import "../styles/BanditMonitor.css";

function BanditMonitor({ banditRows, armLabels }) {
  const [openState, setOpenState] = useState(
    banditRows[0]?.state ?? null
  );

  return (
    <aside className="monitor-panel">
      <div className="monitor-header">
        <div>
          <p className="eyebrow">Bandit Monitor</p>
          <h2>Live Routing</h2>
        </div>

        <span className="monitor-pill">
          GET /bandit
        </span>
      </div>

      <div className="monitor-content">
        {banditRows.map((row) => {
          const expanded = openState === row.state;

          return (
            <div
              key={row.state}
              className="accordion"
            >
              <button
                className="accordion-header"
                onClick={() =>
                  setOpenState(
                    expanded ? null : row.state
                  )
                }
              >
                <div>
                  <strong>{row.state}</strong>
                </div>

                <div className="accordion-right">
                  <span>{row.arms.length} arms</span>

                  <span
                    className={`arrow ${
                      expanded ? "open" : ""
                    }`}
                  >
                    ▼
                  </span>
                </div>
              </button>

              {expanded && (
                <div className="accordion-body">
                  <div className="arm-grid">
                    {armLabels.map((label) => {
                      const arm = row.arms.find(
                        (a) => a.label === label
                      );

                      if (!arm) return null;

                      const [model, topk] =
                        label.split("|");

                      return (
                        <div
                          className="arm-card"
                          key={label}
                        >
                          <h4>{model}</h4>

                          <small>{topk}</small>

                          <div className="arm-metrics">
                            <div>
                              <span>Q</span>

                              <strong>
                                {arm.value.q.toFixed(2)}
                              </strong>
                            </div>

                            <div>
                              <span>Samples</span>

                              <strong>
                                {arm.value.n}
                              </strong>
                            </div>
                          </div>
                        </div>
                      );
                    })}
                  </div>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </aside>
  );
}

export default BanditMonitor;