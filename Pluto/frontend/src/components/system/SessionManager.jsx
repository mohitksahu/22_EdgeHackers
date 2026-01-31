/**
 * SessionManager Component
 * Displays session info and provides clear/new session actions
 */
import { useState, useEffect } from 'react';
import { getSessionId, getSessionInfo, clearSession, createNewSession } from '../../services/sessionService';

function SessionManager({ onSessionChange }) {
  const [sessionId, setSessionId] = useState('');
  const [sessionInfo, setSessionInfo] = useState(null);
  const [isExpanded, setIsExpanded] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadSessionInfo();
  }, []);

  const loadSessionInfo = async () => {
    const currentSessionId = getSessionId();
    setSessionId(currentSessionId);
    
    try {
      const info = await getSessionInfo();
      setSessionInfo(info);
    } catch (error) {
      console.error('Failed to load session info:', error);
    }
  };

  const handleClearSession = async () => {
    if (!confirm('Are you sure you want to clear this session? This will delete all documents and conversation history.')) {
      return;
    }

    setLoading(true);
    try {
      await clearSession();
      await loadSessionInfo();
      if (onSessionChange) onSessionChange();
      alert('Session cleared successfully!');
    } catch (error) {
      console.error('Failed to clear session:', error);
      alert('Failed to clear session. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleNewSession = () => {
    if (sessionInfo?.chat_history?.turn_count > 0 || sessionInfo?.document_count > 0) {
      if (!confirm('Start a new session? Your current conversation and documents will remain in the old session.')) {
        return;
      }
    }

    const newId = createNewSession();
    setSessionId(newId);
    setSessionInfo(null);
    if (onSessionChange) onSessionChange();
    alert(`New session created: ${newId.substring(0, 20)}...`);
  };

  const formatSessionId = (id) => {
    if (!id) return '';
    return id.length > 25 ? `${id.substring(0, 25)}...` : id;
  };

  return (
    <div className="mb-6 card border-gray-300 dark:border-gray-700">
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
          <h3 className="text-lg font-semibold">Session Manager</h3>
        </div>
        <div className="flex items-center gap-2 text-sm text-gray-500">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
          </svg>
          <span>{formatSessionId(sessionId)}</span>
        </div>
      </button>

      {isExpanded && (
        <div className="px-4 pb-4 space-y-4 border-t border-gray-200 dark:border-gray-700 pt-4">
          {/* Session Info */}
          <div className="grid grid-cols-2 gap-3 text-sm">
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded p-3">
              <div className="text-gray-500 dark:text-gray-400 text-xs mb-1">Documents</div>
              <div className="text-2xl font-bold text-blue-600 dark:text-blue-400">
                {sessionInfo?.document_count || 0}
              </div>
            </div>
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded p-3">
              <div className="text-gray-500 dark:text-gray-400 text-xs mb-1">Conversations</div>
              <div className="text-2xl font-bold text-green-600 dark:text-green-400">
                {sessionInfo?.chat_history?.turn_count || 0}
              </div>
            </div>
          </div>

          {/* Session ID */}
          <div>
            <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Session ID</div>
            <div className="bg-gray-100 dark:bg-gray-800 rounded px-3 py-2 font-mono text-xs break-all">
              {sessionId}
            </div>
          </div>

          {/* Last Activity */}
          {sessionInfo?.chat_history?.last_timestamp && (
            <div>
              <div className="text-xs text-gray-500 dark:text-gray-400 mb-1">Last Activity</div>
              <div className="text-sm">
                {new Date(sessionInfo.chat_history.last_timestamp).toLocaleString()}
              </div>
            </div>
          )}

          {/* Actions */}
          <div className="flex gap-3 pt-2">
            <button
              onClick={handleNewSession}
              className="flex-1 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded transition-colors flex items-center justify-center gap-2"
              disabled={loading}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
              New Session
            </button>
            
            <button
              onClick={handleClearSession}
              className="flex-1 px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded transition-colors flex items-center justify-center gap-2"
              disabled={loading}
            >
              {loading ? (
                <div className="animate-spin w-4 h-4 border-2 border-white border-t-transparent rounded-full"></div>
              ) : (
                <>
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                  Clear Session
                </>
              )}
            </button>
          </div>

          <div className="text-xs text-gray-500 dark:text-gray-400 bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 dark:border-yellow-800 rounded p-2">
            💡 <strong>Tip:</strong> Sessions isolate your documents and conversations. Create a new session for different projects.
          </div>
        </div>
      )}
    </div>
  );
}

export default SessionManager;
