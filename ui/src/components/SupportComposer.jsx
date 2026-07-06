import { useEffect, useRef } from 'react'
import '../styles/SupportComposer.css'

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
  const textareaRef = useRef(null)

  useEffect(() => {
    if (!textareaRef.current) return

    textareaRef.current.style.height = '0px'
    textareaRef.current.style.height = `${Math.min(
      textareaRef.current.scrollHeight,
      220,
    )}px`
  }, [query])

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()

      if (!isLoading && query.trim()) {
        onSubmit(e)
      }
    }
  }

  return (
    <form className="composer" onSubmit={onSubmit}>
      <div className="composer-shell">
        <textarea
          ref={textareaRef}
          value={query}
          rows={1}
          placeholder="Ask a support question..."
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
        />

        <button
          className="send-button"
          type="submit"
          disabled={isLoading || !query.trim()}
        >
          {isLoading ? (
            <span className="loader" />
          ) : (
            <span>➜</span>
          )}
        </button>
      </div>

      <div className="composer-footer">
        <button
          type="button"
          className="advanced-toggle"
          onClick={() => setAdvancedOpen((prev) => !prev)}
        >
          ⚙ {advancedOpen ? 'Hide Advanced' : 'Advanced'}
        </button>

        {advancedOpen && (
          <div className="advanced-controls">
            <label>
              <span>Model</span>

              <select
                value={modelOverride}
                onChange={(e) => setModelOverride(e.target.value)}
              >
                <option value="auto">Auto (Bandit)</option>
                <option value="llama3.2:3b">llama3.2:3b</option>
                <option value="qwen2.5:3b">qwen2.5:3b</option>
              </select>
            </label>

            <label>
              <span>Top-k</span>

              <select
                value={topKOverride}
                onChange={(e) => setTopKOverride(e.target.value)}
              >
                <option value="auto">Auto</option>
                <option value="2">2</option>
                <option value="5">5</option>
              </select>
            </label>
          </div>
        )}
      </div>
    </form>
  )
}

export default SupportComposer