function SupportComposer({
  query,
  setQuery,
  onSubmit,
  isLoading,
  advancedOpen,
  setAdvancedOpen,
  modelOverride,
  setModelOverride,
  topKOverride,
  setTopKOverride,
}) {
  return (
    <form className="composer" onSubmit={onSubmit}>
      <textarea
        rows={3}
        value={query}
        onChange={(event) => setQuery(event.target.value)}
        placeholder="Ask a support question..."
      />
      <div className="composer-actions">
        <button type="button" className="secondary-button" onClick={() => setAdvancedOpen((open) => !open)}>
          {advancedOpen ? 'Hide advanced' : 'Advanced'}
        </button>
        <button type="submit" className="primary-button" disabled={isLoading}>
          {isLoading ? 'Asking…' : 'Ask'}
        </button>
      </div>
      {advancedOpen && (
        <div className="advanced-controls">
          <label>
            <span>Model</span>
            <select value={modelOverride} onChange={(event) => setModelOverride(event.target.value)}>
              <option value="auto">Auto (bandit)</option>
              <option value="llama3.2:3b">llama3.2:3b</option>
              <option value="qwen2.5:3b">qwen2.5:3b</option>
            </select>
          </label>
          <label>
            <span>Top-k</span>
            <select value={topKOverride} onChange={(event) => setTopKOverride(event.target.value)}>
              <option value="auto">Auto</option>
              <option value="2">2</option>
              <option value="5">5</option>
            </select>
          </label>
        </div>
      )}
    </form>
  )
}

export default SupportComposer
