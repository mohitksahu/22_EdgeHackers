/**
 * ChatHistory Component
 * Displays conversation history with expand/collapse and themed styling
 */
import { useState, useEffect } from 'react';
import { getSessionInfo } from '../../services/sessionService';

function ChatHistory({ onSelectTurn }) {
  const [history, setHistory] = useState([]);
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);
  const [turnCount, setTurnCount] = useState(0);

  useEffect(() => {
    loadHistory();
  }, []);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const sessionInfo = await getSessionInfo();
      const chatHistory = sessionInfo.chat_history || {};
      setTurnCount(chatHistory.turn_count || 0);
      
      // Note: Backend doesn't return full turns in session/info
      // We'll show metadata only. For full history, would need separate endpoint
    } catch (error) {
      console.error('Failed to load chat history:', error);
    } finally {
      setLoading(false);
    }
  };

  if (turnCount === 0) {
    return null; // Don't show if no history
  }

  return (
    <div className="mb-6 card">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between p-4 hover:bg-gray-50 dark:hover:bg-gray-800/50 transition-colors rounded"
      >
        <div className="flex items-center gap-3">
          <svg 
            className={`w-5 h-5 transition-transform ${isExpanded ? 'rotate-90' : ''}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <h3 className="text-lg font-semibold">Conversation History</h3>
          <span className="text-sm text-gray-500 bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">
            {turnCount} {turnCount === 1 ? 'turn' : 'turns'}
          </span>
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-3">
          <div className="text-sm text-gray-600 dark:text-gray-400 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded p-3">
            <p className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>Your conversation is being tracked. You can ask follow-up questions using "it", "that", or "those".</span>
            </p>
            <p className="mt-2 text-xs">
              <strong>Example:</strong> "What is the nervous system?" → "What are its main components?"
            </p>
          </div>

          {loading ? (
            <div className="text-center py-4 text-gray-500">
              <div className="animate-spin w-6 h-6 border-2 border-gray-300 border-t-blue-500 rounded-full mx-auto"></div>
              <p className="mt-2 text-sm">Loading history...</p>
            </div>
          ) : (
            <div className="text-sm text-gray-600 dark:text-gray-400">
              <p>Previous conversations are used to provide context for your follow-up questions.</p>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ChatHistory;
