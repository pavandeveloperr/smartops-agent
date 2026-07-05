export function buildBanditRows(bandit, armLabels) {
  if (!bandit) {
    return []
  }

  return Object.entries(bandit).map(([state, arms]) => ({
    state,
    arms: armLabels.map((label) => ({
      label,
      value: arms[label] || { q: 0, n: 0 },
    })),
  }))
}
