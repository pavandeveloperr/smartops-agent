import { useEffect, useMemo, useState } from 'react'
import './App.css'
import { askSupport, fetchBanditSnapshot, fetchHealth, submitFeedback } from './api'
import BanditMonitor from './components/BanditMonitor'
import MessageCard from './components/MessageCard'
import SupportComposer from './components/SupportComposer'
import { buildBanditRows } from './utils'

const ARM_LABELS = ['llama3.2:3b|k=2', 'llama3.2:3b|k=5', 'qwen2.5:3b|k=2', 'qwen2.5:3b|k=5']

function App() {
  const [query, setQuery] = useState('How do I fix error E-101?')
  const [messages, setMessages] = useState([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [healthStatus, setHealthStatus] = useState('checking')
  const [bandit, setBandit] = useState(null)
  const [advancedOpen, setAdvancedOpen] = useState(false)
  const [modelOverride, setModelOverride] = useState('auto')
  const [topKOverride, setTopKOverride] = useState('auto')
  const [feedbackMap, setFeedbackMap] = useState({})

  const loadBanditSnapshot = async () => {
    try {
      const snapshot = await fetchBanditSnapshot()
      setBandit(snapshot)
    } catch {
      // keep previous state if the monitor request fails
    }
  }

  useEffect(() => {
    const init = async () => {
      try {
        await fetchHealth()
        setHealthStatus('online')
        await loadBanditSnapshot()
      } catch {
        setHealthStatus('offline')
        setError('The API is not reachable. Start the FastAPI server on port 8000 first.')
      }
    }

    init()
  }, [])

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!query.trim()) {
      return
    }

    setIsLoading(true)
    setError('')

    const userMessage = { type: 'user', content: query }
    setMessages((current) => [...current, userMessage])

    try {
      const data = await askSupport({
        query,
        model: modelOverride,
        top_k: topKOverride,
      })

      const assistantMessage = {
        type: 'assistant',
        id: data.transaction_id,
        answer: data.answer,
        llmUsed: data.llm_used,
        latencySeconds: data.latency_seconds,
        sources: data.sources,
      }

      setMessages((current) => [...current, assistantMessage])
      setQuery('')
      await loadBanditSnapshot()
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFeedback = async (transactionId, score) => {
    setFeedbackMap((current) => ({ ...current, [transactionId]: 'submitting' }))

    try {
      await submitFeedback(transactionId, score)
      setFeedbackMap((current) => ({ ...current, [transactionId]: score === 1 ? 'up' : 'down' }))
      setMessages((current) =>
        current.map((message) =>
          message.id === transactionId ? { ...message, feedback: score === 1 ? 'up' : 'down' } : message,
        ),
      )
      await loadBanditSnapshot()
    } catch (err) {
      setFeedbackMap((current) => ({ ...current, [transactionId]: 'error' }))
      setError(err.message)
    }
  }

  const banditRows = useMemo(() => buildBanditRows(bandit, ARM_LABELS), [bandit])

  return (
    <div className="app-shell">
      <header className="app-header">
        <div>
          <p className="eyebrow">SmartOps technical support</p>
          <h1>Self-optimizing support agent</h1>
          <p className="subtle-text">
            Ask a question, inspect the routed answer, and score it so the bandit learns which model and retrieval depth work best.
          </p>
        </div>
        <div className="health-card">
          <span className={`status-dot ${healthStatus}`} />
          <strong>{healthStatus === 'online' ? 'Backend online' : 'Backend offline'}</strong>
          <span>API: {import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000'}</span>
        </div>
      </header>

      <main className="content-grid">
        <section className="chat-panel">
          <SupportComposer
            query={query}
            setQuery={setQuery}
            onSubmit={handleSubmit}
            isLoading={isLoading}
            advancedOpen={advancedOpen}
            setAdvancedOpen={setAdvancedOpen}
            modelOverride={modelOverride}
            setModelOverride={setModelOverride}
            topKOverride={topKOverride}
            setTopKOverride={setTopKOverride}
          />

          {error && <div className="error-banner">{error}</div>}

          <div className="transcript">
            {messages.length === 0 && !isLoading && (
              <div className="empty-state">
                <p>Use the composer to ask the agent a support question.</p>
                <p className="hint">The answer card includes feedback controls so the RL loop can learn from every interaction.</p>
              </div>
            )}

            {messages.map((message, index) => (
              <MessageCard
                key={`${message.type}-${index}`}
                message={message}
                feedbackMap={feedbackMap}
                onFeedback={handleFeedback}
              />
            ))}

            {isLoading && (
              <div className="message-card assistant pending">
                <div className="message-meta">
                  <strong>Agent</strong>
                  <span>Thinking…</span>
                </div>
                <div className="skeleton" />
                <div className="skeleton short" />
              </div>
            )}
          </div>
        </section>

        <BanditMonitor banditRows={banditRows} armLabels={ARM_LABELS} />
      </main>
    </div>
  )
}

export default App
