import { useState, useRef, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogClose,
} from '../common/Dialog';

export default function CenterPanel({ messages, onSendMessage, leftPanelOpen, rightPanelOpen, isLoading, pageName, onPageNameChange, isMobile }) {
  const [inputValue, setInputValue] = useState('');
  const [isRenameDialogOpen, setIsRenameDialogOpen] = useState(false);
  const [tempTitle, setTempTitle] = useState(pageName);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  useEffect(() => {
    setTempTitle(pageName);
  }, [pageName]);

  const handleTitleClick = () => {
    setTempTitle(pageName);
    setIsRenameDialogOpen(true);
  };

  const handleRenameSubmit = () => {
    const newName = tempTitle.trim();
    // Only allow storing with new names (not "Untitled Planet")
    if (newName && newName !== 'Untitled Planet') {
      onPageNameChange(newName);
      setIsRenameDialogOpen(false);
    }
  };

  const handleRenameCancel = () => {
    setTempTitle(pageName);
    setIsRenameDialogOpen(false);
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (inputValue.trim()) {
      onSendMessage(inputValue);
      setInputValue('');
    }
  };

  return (
    <main className={`
      flex-1 flex flex-col h-full border border-[var(--card-border,#1f1f2e)] bg-[var(--card-bg,#14141f)]/30
      ${isMobile ? 'mx-2' : leftPanelOpen ? 'ml-3 mr-3' : rightPanelOpen ? 'ml-3 mr-3' : 'mx-3'}
      transition-all duration-300
    `}>
      {/* Page Title Header with Status Badge */}
      <div className="px-6 pt-6 pb-3 border-b border-[var(--card-border,#1f1f2e)]">
        <div className="flex items-center justify-between gap-4">
          <div className="flex-1 min-w-0 flex items-center gap-3">
            <h1 className="text-lg font-medium text-[var(--text-color)] truncate">
              {pageName}
            </h1>
            <button
              onClick={handleTitleClick}
              className="flex-shrink-0 p-1.5 rounded-md hover:bg-[var(--card-border,#1f1f2e)]/50 transition-colors group relative"
            >
              <svg
                className="w-4 h-4 text-[var(--text-secondary,#8b8b9f)] group-hover:text-[var(--text-color)] transition-colors"
                fill="none"
                viewBox="0 0 24 24"
                stroke="currentColor"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"
                />
              </svg>
              {/* Tooltip */}
              <div className="absolute top-1/2 left-full transform -translate-y-1/2 ml-2 px-2 py-1 bg-[var(--card-bg,#14141f)] text-[var(--text-color)] text-xs rounded-md border border-[var(--card-border,#1f1f2e)] opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-10">
                Rename
                <div className="absolute top-1/2 right-full transform translate-y-1/2 mr-1 border-t-4 border-b-4 border-l-4 border-transparent border-l-[var(--card-bg,#14141f)]"></div>
              </div>
            </button>
          </div>
          
          {/* Status Badge */}
          <div className="flex-shrink-0">
            <div className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-[var(--card-bg,#14141f)]/50 border border-pluto-purple/20">
              <span className="w-1.5 h-1.5 rounded-full bg-pluto-purple animate-pulse"></span>
              <span className="text-xs font-medium text-pluto-purple/90">Offline RAG Active</span>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto mb-4">
        {messages.length === 0 && !isLoading ? (
          /* Empty State - Minimal Placeholder */
          <div className="h-full flex items-center justify-center">
            <p className="text-[var(--secondary-text,#9ca3af)] text-sm">
              Ask a question to begin…
            </p>
          </div>
        ) : (
          /* Chat Messages */
          <div className="space-y-6 px-6 py-6">
            {messages.map((message) => (
              <div key={message.id} className={`
                ${message.type === 'user' ? 'flex justify-end' : 'flex justify-start'}
              `}>
                {message.type === 'user' ? (
                  /* User Message */
                  <div className="max-w-2xl">
                    <div className="flex items-start gap-3 justify-end">
                      <div className="bg-[var(--card-bg,#14141f)] rounded-2xl px-5 py-3 border border-[var(--card-border,#1f1f2e)]">
                        <p className="text-[var(--text-color,#e5e7eb)] text-sm leading-relaxed">
                          {message.content}
                        </p>
                      </div>
                      <div className="w-8 h-8 rounded-full bg-gradient-to-br from-pluto-purple to-pluto-purple-dark flex items-center justify-center text-white text-xs font-medium flex-shrink-0">
                        U
                      </div>
                    </div>
                  </div>
                ) : (
                  /* AI Response */
                  <div className="max-w-3xl">
                    <div className="flex items-start gap-3">
                      <div className="w-8 h-8 rounded-full bg-[var(--card-bg,#14141f)] border border-[var(--card-border,#1f1f2e)] flex items-center justify-center flex-shrink-0">
                        <svg className="w-4 h-4 text-pluto-purple" fill="currentColor" viewBox="0 0 20 20">
                          <path d="M10 3.5a1.5 1.5 0 013 0V4a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-.5a1.5 1.5 0 000 3h.5a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-.5a1.5 1.5 0 00-3 0v.5a1 1 0 01-1 1H6a1 1 0 01-1-1v-3a1 1 0 00-1-1h-.5a1.5 1.5 0 010-3H4a1 1 0 001-1V6a1 1 0 011-1h3a1 1 0 001-1v-.5z" />
                        </svg>
                      </div>
                      <div className="flex-1">
                        <div className="bg-[var(--card-bg,#14141f)]/50 backdrop-blur-glass rounded-2xl px-5 py-4 border border-[var(--card-border,#1f1f2e)]">
                          {/* Response Content */}
                          <div className="text-[var(--text-color,#e5e7eb)] text-sm leading-relaxed space-y-2">
                            {(message.content || '').split('\n').map((line, idx) => {
                              if (line.startsWith('•')) {
                                return (
                                  <div key={idx} className="flex items-start gap-2 ml-2">
                                    <span className="text-pluto-purple mt-1.5">•</span>
                                    <span>{line.substring(2)}</span>
                                  </div>
                                );
                              }
                              return line ? <p key={idx}>{line}</p> : <br key={idx} />;
                            })}
                          </div>

                          {/* Processing Time */}
                          {message.processingTime && (
                            <div className="mt-3 text-xs text-[var(--secondary-text,#9ca3af)] italic">
                              ⚡ Processed in {message.processingTime}s
                            </div>
                          )}

                          {/* Source Citations */}
                          {message.citations && message.citations.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-4 pt-4 border-t border-[var(--card-border,#1f1f2e)]">
                              {message.citations.map((citation, idx) => (
                                <button
                                  key={idx}
                                  className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-[var(--card-bg,#14141f)] border border-[var(--card-border,#1f1f2e)] hover:border-pluto-purple/50 text-xs text-[var(--secondary-text,#9ca3af)] hover:text-pluto-purple transition-all duration-200"
                                >
                                  <svg className="w-3 h-3" fill="currentColor" viewBox="0 0 20 20">
                                    <path d="M9 4.804A7.968 7.968 0 005.5 4c-1.255 0-2.443.29-3.5.804v10A7.969 7.969 0 015.5 14c1.669 0 3.218.51 4.5 1.385A7.962 7.962 0 0114.5 14c1.255 0 2.443.29 3.5.804v-10A7.968 7.968 0 0014.5 4c-1.255 0-2.443.29-3.5.804V12a1 1 0 11-2 0V4.804z" />
                                  </svg>
                                  {citation}
                                </button>
                              ))}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            ))}
            
            {/* Loading Indicator */}
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-3xl">
                  <div className="flex items-start gap-3">
                    <div className="w-8 h-8 rounded-full bg-[var(--card-bg,#14141f)] border border-[var(--card-border,#1f1f2e)] flex items-center justify-center flex-shrink-0">
                      <svg className="w-4 h-4 text-pluto-purple" fill="currentColor" viewBox="0 0 20 20">
                        <path d="M10 3.5a1.5 1.5 0 013 0V4a1 1 0 001 1h3a1 1 0 011 1v3a1 1 0 01-1 1h-.5a1.5 1.5 0 000 3h.5a1 1 0 011 1v3a1 1 0 01-1 1h-3a1 1 0 01-1-1v-.5a1.5 1.5 0 00-3 0v.5a1 1 0 01-1 1H6a1 1 0 01-1-1v-3a1 1 0 00-1-1h-.5a1.5 1.5 0 010-3H4a1 1 0 001-1V6a1 1 0 011-1h3a1 1 0 001-1v-.5z" />
                      </svg>
                    </div>
                    <div className="flex-1">
                      <div className="bg-[var(--card-bg,#14141f)]/50 backdrop-blur-glass rounded-2xl px-5 py-4 border border-[var(--card-border,#1f1f2e)]">
                        <div className="flex items-center gap-2">
                          <div className="w-2 h-2 bg-pluto-purple rounded-full animate-pulse-slow"></div>
                          <div className="w-2 h-2 bg-pluto-purple rounded-full animate-pulse-slow" style={{ animationDelay: '0.2s' }}></div>
                          <div className="w-2 h-2 bg-pluto-purple rounded-full animate-pulse-slow" style={{ animationDelay: '0.4s' }}></div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input Bar */}
      <div className="px-6 pb-6">
        <form onSubmit={handleSubmit} className="relative">
          <div className="relative">
            <input
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              placeholder="Ask a question grounded in your sources…"
              className="w-full px-5 py-4 pr-12 rounded-2xl bg-[var(--card-bg,#14141f)] border border-[var(--card-border,#1f1f2e)] focus:border-pluto-purple focus:ring-2 focus:ring-pluto-purple/20 text-[var(--text-color,#e5e7eb)] placeholder-[var(--secondary-text,#9ca3af)] outline-none transition-all duration-200"
            />
            <button
              type="submit"
              disabled={!inputValue.trim()}
              className="absolute right-3 top-1/2 -translate-y-1/2 p-2 rounded-xl bg-pluto-purple hover:bg-pluto-purple-dark disabled:opacity-50 disabled:cursor-not-allowed text-white transition-all duration-200"
              aria-label="Send message"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            </button>
          </div>
        </form>
      </div>

      {/* Rename Dialog */}
      <Dialog open={isRenameDialogOpen} onOpenChange={setIsRenameDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Rename Page</DialogTitle>
            <DialogDescription>
              Enter a new name for this page. Names must be different from "Untitled Planet" to be saved.
            </DialogDescription>
          </DialogHeader>
          <div className="px-8 pb-8">
            <div className="space-y-6">
              <div className="space-y-2">
                <label htmlFor="pageName" className="block text-sm font-medium text-[var(--text-color)]">
                  Page Name
                </label>
                <input
                  id="pageName"
                  type="text"
                  value={tempTitle}
                  onChange={(e) => setTempTitle(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') {
                      handleRenameSubmit();
                    } else if (e.key === 'Escape') {
                      handleRenameCancel();
                    }
                  }}
                  className="w-full h-11 rounded-lg border border-[var(--card-border,#1f1f2e)] bg-[var(--card-bg,#14141f)] px-4 text-base text-[var(--text-color)] outline-none focus:ring-2 focus:ring-pluto-purple/50 focus:border-pluto-purple transition-colors"
                  placeholder="Enter page name"
                  autoFocus
                />
              </div>
              <div className="flex justify-end gap-3">
                <button
                  onClick={handleRenameCancel}
                  className="px-4 py-2.5 text-sm font-medium text-[var(--text-color)] bg-transparent border border-[var(--card-border,#1f1f2e)] rounded-lg hover:bg-[var(--card-border,#1f1f2e)]/50 transition-colors"
                >
                  Cancel
                </button>
                <button
                  onClick={handleRenameSubmit}
                  disabled={!tempTitle.trim() || tempTitle.trim() === 'Untitled Planet'}
                  className="px-4 py-2.5 text-sm font-medium text-white bg-pluto-purple rounded-lg hover:bg-pluto-purple-dark disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                >
                  Rename
                </button>
              </div>
            </div>
          </div>
          <DialogClose onClick={handleRenameCancel} />
        </DialogContent>
      </Dialog>
    </main>
  );
}
