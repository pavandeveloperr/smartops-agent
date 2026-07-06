import "../styles/MessageCard.css";

function MessageCard({ message, feedbackMap, onFeedback }) {
  const isUser = message.type === "user";

  const isFeedbackPending = feedbackMap[message.id] === "submitting";
  const isFeedbackUp = feedbackMap[message.id] === "up";
  const isFeedbackDown = feedbackMap[message.id] === "down";

  return (
    <div className={`message-row ${isUser ? "user" : "assistant"}`}>
      <div className={`message-bubble ${isUser ? "user" : "assistant"}`}>
        <div className="message-meta">
          <div className="message-author">
            <span className="avatar">
              {isUser ? "👤" : "🤖"}
            </span>

            <strong>
              {isUser ? "You" : "Agent"}
            </strong>

            {!isUser && (
              <span className="message-model">
                {message.llmUsed} • {message.latencySeconds?.toFixed(2)}s
              </span>
            )}
          </div>
        </div>

        {isUser ? (
          <p>{message.content}</p>
        ) : (
          <>
            <div className="message-content">
              {message.answer}
            </div>

            {message.sources?.length > 0 && (
              <div className="source-list">
                {message.sources.map((source) => (
                  <span key={source} className="chip">
                    {source}
                  </span>
                ))}
              </div>
            )}

            <div className="feedback-row">
              <button
                className="feedback-button"
                disabled={
                  isFeedbackPending ||
                  isFeedbackUp ||
                  isFeedbackDown
                }
                onClick={() => onFeedback(message.id, 1)}
              >
                👍
              </button>

              <button
                className="feedback-button"
                disabled={
                  isFeedbackPending ||
                  isFeedbackUp ||
                  isFeedbackDown
                }
                onClick={() => onFeedback(message.id, 0)}
              >
                👎
              </button>

              {isFeedbackPending && (
                <span className="feedback-state">
                  Saving...
                </span>
              )}

              {isFeedbackUp && (
                <span className="feedback-state positive">
                  Thanks!
                </span>
              )}

              {isFeedbackDown && (
                <span className="feedback-state negative">
                  Feedback recorded
                </span>
              )}
            </div>
          </>
        )}
      </div>
    </div>
  );
}

export default MessageCard;