function MessageCard({ message, feedbackMap, onFeedback }) {
  const isFeedbackPending = feedbackMap[message.id] === 'submitting'
  const isFeedbackUp = feedbackMap[message.id] === 'up'
  const isFeedbackDown = feedbackMap[message.id] === 'down'

  return (
    <div className={`message-card ${message.type}`}>
      <div className="message-meta">
        <strong>{message.type === 'user' ? 'You' : 'Agent'}</strong>
        {message.type === 'assistant' && (
          <span>
            {message.llmUsed} · k={message.sources?.length ? 'auto' : 'n/a'} · {message.latencySeconds?.toFixed(2)}s
          </span>
        )}
      </div>
      {message.type === 'user' ? (
        <p>{message.content}</p>
      ) : (
        <>
          <p>{message.answer}</p>
          {message.sources?.length > 0 && (
            <div className="source-list">
              <span className="label">Sources</span>
              {message.sources.map((source) => (
                <span key={source} className="chip">
                  {source}
                </span>
              ))}
            </div>
          )}
          <div className="feedback-row">
            <span className="label">Was this useful?</span>
            <button
              type="button"
              className="feedback-button"
              onClick={() => onFeedback(message.id, 1)}
              disabled={isFeedbackPending || isFeedbackUp || isFeedbackDown}
            >
              👍 Yes
            </button>
            <button
              type="button"
              className="feedback-button"
              onClick={() => onFeedback(message.id, 0)}
              disabled={isFeedbackPending || isFeedbackUp || isFeedbackDown}
            >
              👎 No
            </button>
            {isFeedbackPending && <span className="feedback-state">Saving…</span>}
            {isFeedbackUp && <span className="feedback-state positive">Thanks for the thumbs up.</span>}
            {isFeedbackDown && <span className="feedback-state negative">Feedback recorded.</span>}
          </div>
        </>
      )}
    </div>
  )
}

export default MessageCard
