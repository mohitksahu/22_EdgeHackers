import React, { useState, useRef, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import '../../styles/Dashboard.css';
import Header from './Header';
import LeftPanel from './LeftPanel';
import CenterPanel from './CenterPanel';
import RightPanel from './RightPanel';
import { uploadSingleFile, uploadBatchFiles } from '../../services/ingestionService';
import { submitQuery } from '../../services/queryService';
import { getSessionId, createNewPlanet, switchToPlanet, deletePlanet, renamePlanet } from '../../services/sessionService';

export default function Dashboard() {
  const location = useLocation();
  const navigate = useNavigate();
  const [leftPanelOpen, setLeftPanelOpen] = useState(true);
  const [rightPanelOpen, setRightPanelOpen] = useState(true);
  const [sources, setSources] = useState([]);
  const [sourcesLoading, setSourcesLoading] = useState(false);
  const [pageName, setPageName] = useState('Untitled Planet');
  const [messages, setMessages] = useState([]);
  const [messagesLoading, setMessagesLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([]);
  const [currentChatId, setCurrentChatId] = useState(null);
  const [evidenceData, setEvidenceData] = useState(null);
  const [evidenceLoading, setEvidenceLoading] = useState(false);
  const [user, setUser] = useState(null); // Backend will provide user data

  // Upload states for real-time progress
  const [uploadProgress, setUploadProgress] = useState({});
  const [uploadingFiles, setUploadingFiles] = useState(new Set());

  const [leftPanelWidth, setLeftPanelWidth] = useState(260);
  const [rightPanelWidth, setRightPanelWidth] = useState(300);
  const [isResizingLeft, setIsResizingLeft] = useState(false);
  const [isResizingRight, setIsResizingRight] = useState(false);
  const containerRef = useRef(null);
  const [isMobile, setIsMobile] = useState(false);

  // Rename modal states
  const [showRenameModal, setShowRenameModal] = useState(false);
  const [newPlanetName, setNewPlanetName] = useState('Untitled Planet');
  const [renameError, setRenameError] = useState('');

  // Exit prompt modal states
  const [showExitPrompt, setShowExitPrompt] = useState(false);
  const [exitAction, setExitAction] = useState('back'); // 'back' or 'newplanet'

  // Handle loading planet from navigation state
  useEffect(() => {
    if (location.state?.loadPlanet) {
      const planet = location.state.loadPlanet;
      setPageName(planet.name);
      setMessages(planet.messages || []);
      setCurrentChatId(planet.id);
      setShowRenameModal(false);
      // Clear the navigation state
      window.history.replaceState({}, document.title);
    } else {
      // New planet, don't show modal yet
      setPageName('Untitled Planet');
      setMessages([]);
      setCurrentChatId(Date.now()); // Generate ID immediately
      setShowRenameModal(false);
      setNewPlanetName('Untitled Planet');
      setRenameError('');
    }
  }, [location.state]);

  // Save planet history with sessionId
  useEffect(() => {
    if (messages.length > 0) {
      const planetHistory = JSON.parse(localStorage.getItem('planetHistory') || '[]');
      const planetData = {
        id: currentChatId || Date.now(),
        sessionId: getSessionId(), // ADD THIS LINE
        name: pageName,
        messages: messages,
        timestamp: new Date().toISOString(),
        sources: sources.length,
      };

      const existingIndex = planetHistory.findIndex(p => p.id === planetData.id);
      if (existingIndex >= 0) {
        planetHistory[existingIndex] = planetData;
      } else {
        planetHistory.unshift(planetData); // Add to beginning
      }

      const trimmedHistory = planetHistory.slice(0, 20);

      localStorage.setItem('planetHistory', JSON.stringify(trimmedHistory));
    }
  }, [messages, sources, pageName, currentChatId]);

  // Responsive panel handling
  React.useEffect(() => {
    const handleResize = () => {
      const width = window.innerWidth;
      
      if (width < 640) {
        // Small screens: panels closed
        setIsMobile(true);
        setLeftPanelOpen(false);
        setRightPanelOpen(false);
        setLeftPanelWidth(200);
        setRightPanelWidth(250);
      } else if (width < 1024) {
        // Medium screens (tablets): panels open but narrower
        setIsMobile(false);
        setLeftPanelOpen(true);
        setRightPanelOpen(true);
        setLeftPanelWidth(220);
        setRightPanelWidth(260);
      } else {
        // Large screens: panels open with full width
        setIsMobile(false);
        setLeftPanelOpen(true);
        setRightPanelOpen(true);
        setLeftPanelWidth(260);
        setRightPanelWidth(300);
      }
    };

    handleResize(); // Set initial state
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleSendMessage = async (message) => {
    // Add user message immediately
    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: message,
      timestamp: new Date(),
    };
    setMessages(prev => [...prev, userMessage]);

    // Add loading indicator message
    const loadingMessage = {
      id: Date.now() + 0.5,
      type: 'ai',
      content: 'Processing your query... This may take a few minutes as the AI analyzes your documents.',
      timestamp: new Date(),
      isLoading: true
    };
    setMessages(prev => [...prev, loadingMessage]);

    // Set loading state
    setMessagesLoading(true);
    setEvidenceLoading(true);
    
    // Clear evidence while loading to prevent showing old data
    setEvidenceData(null);

    const startTime = Date.now();

    try {
      // Call backend API with extended timeout handling
      const response = await submitQuery(message);
      
      // Debug: Log full API response
      console.log("FULL API RESPONSE:", response);

      const processingTime = ((Date.now() - startTime) / 1000).toFixed(1);

      // Check for refusal first
      let content;
      let isRefusal = false;
      
      if (response.refusal) {
        content = response.refusal;
        isRefusal = true;
      } else {
        content = response.response || 'No response received';
      }

      // FIX: Properly extract citations from sources (which are now objects)
      const sourcesArray = response.sources || [];
      const citations = sourcesArray.map(source => {
        if (typeof source === 'string') return source;
        return source.file || source.file_name || source.filename || 'Unknown';
      });

      // Create AI message with typing effect flag
      const aiMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: content,
        timestamp: new Date(),
        citations: citations,
        processingTime: processingTime,
        isTyping: true  // Flag for typing animation
      };
      
      // First, update messages to show the AI response
      setMessages(prev => prev.filter(msg => !msg.isLoading).concat(aiMessage));

      // After typing animation completes, update the message
      const typingDuration = Math.min(content.length * 15, 3000); // Max 3 seconds
      setTimeout(() => {
        setMessages(prev => prev.map(msg => 
          msg.id === aiMessage.id ? { ...msg, isTyping: false } : msg
        ));
      }, typingDuration);
      
      // Wait a brief moment before showing evidence (better UX)
      setTimeout(() => {
        // Build evidence cards from sources (which are objects)
        const evidenceCards = sourcesArray.map((source, index) => {
          // Handle both string and object sources
          const filename = typeof source === 'string' 
            ? source 
            : (source.file || source.file_name || source.filename || 'Unknown');
          const score = typeof source === 'object' ? (source.score || 0) : 0;
          const modality = typeof source === 'object' ? (source.modality || 'text') : 'text';
          const page = typeof source === 'object' ? source.page : null;
          
          // Convert score (0-1) to percentage
          const confidencePercent = Math.round(score * 100);
          
          return {
            id: index,
            filename: filename,
            timestamp: 'Just now',
            confidence: confidencePercent,
            excerpt: page ? `Page ${page}` : '',
            modality: modality,
            fileType: modality
          };
        });

        // Use global confidence from response (convert 0-1 to 0-100 if needed)
        const rawConfidence = response.confidence_score ?? response.confidence ?? 0;
        const globalConfidence = rawConfidence > 1 ? rawConfidence : Math.round(rawConfidence * 100);

        setEvidenceData({
          confidence: globalConfidence,
          sources: sourcesArray.length,
          cards: evidenceCards,
          conflictsDetected: response.has_conflicts || response.conflicts_detected || false,
          conflicts: response.conflicts || []
        });
        
        setEvidenceLoading(false);
      }, 300); // 300ms delay for smoother UX

    } catch (error) {
      console.error('Query failed:', error);

      // Determine error message based on error type
      let errorContent = 'Sorry, I encountered an error processing your query.';
      
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        errorContent = 'The query is taking longer than expected. The backend might still be processing. Please try a simpler query or wait a moment and try again.';
      } else if (error.response) {
        errorContent = `Error: ${error.response.data?.detail || error.response.statusText || 'Server error occurred'}`;
      } else if (error.request) {
        errorContent = 'Unable to reach the server. Please ensure the backend is running and try again.';
      }

      // Remove loading message and add error message
      const errorMessage = {
        id: Date.now() + 1,
        type: 'ai',
        content: errorContent,
        timestamp: new Date(),
        isError: true
      };

      // Note: evidenceLoading is set to false in the setTimeout above for success case
      // For error case, set it here
      if (!evidenceData) {
        setEvidenceLoading(false);
      }
      setMessages(prev => prev.filter(msg => !msg.isLoading).concat(errorMessage));

      // Clear evidence on error
      setEvidenceData(null);
    } finally {
      setMessagesLoading(false);
      setEvidenceLoading(false);
    }
  };

  const handleFileUpload = async (files) => {
    const fileArray = Array.from(files);

    // Add files to uploading state for progress tracking
    const fileIds = fileArray.map(file => `${file.name}-${Date.now()}`);
    setUploadingFiles(prev => new Set([...prev, ...fileIds]));

    // Initialize progress for each file
    const initialProgress = {};
    fileIds.forEach(id => {
      initialProgress[id] = { status: 'uploading', progress: 0, error: null };
    });
    setUploadProgress(prev => ({ ...prev, ...initialProgress }));

    try {
      if (fileArray.length === 1) {
        // Single file upload
        const file = fileArray[0];
        const fileId = fileIds[0];

        // Update progress to processing
        setUploadProgress(prev => ({
          ...prev,
          [fileId]: { status: 'processing', progress: 50, error: null }
        }));

        const result = await uploadSingleFile(file, {
          chunking_strategy: 'character',
          chunk_size: 1000,
          chunk_overlap: 200
        });

        // Update progress to completed
        setUploadProgress(prev => ({
          ...prev,
          [fileId]: { status: 'completed', progress: 100, error: null }
        }));

        // Add to sources
        const newSource = {
          id: Date.now(),
          name: file.name,
          timestamp: 'Just uploaded',
          type: file.type.includes('pdf') ? 'pdf' : file.type.includes('image') ? 'image' : 'doc',
          status: 'completed',
          chunks: result.chunks || result.indexed || 0,  // Fixed: use 'chunks' not 'stored_chunks'
          modality: result.modality || 'text'
        };
        setSources(prev => [newSource, ...prev]);

      } else {
        // Batch upload
        const results = await uploadBatchFiles(fileArray, {
          chunking_strategy: 'character',
          chunk_size: 1000,
          chunk_overlap: 200
        });

        // Update progress for all files
        fileIds.forEach((fileId, index) => {
          const result = results[index];
          setUploadProgress(prev => ({
            ...prev,
            [fileId]: {
              status: 'completed',
              progress: 100,
              error: null
            }
          }));

          // Add to sources
          const file = fileArray[index];
          const newSource = {
            id: Date.now() + index,
            name: file.name,
            timestamp: 'Just uploaded',
            type: file.type.includes('pdf') ? 'pdf' : file.type.includes('image') ? 'image' : 'doc',
            status: 'completed',
            chunks: result?.chunks || result?.indexed || 0,  // Fixed: use 'chunks' not 'stored_chunks'
            modality: result?.modality || 'text'
          };
          setSources(prev => [newSource, ...prev]);
        });
      }

    } catch (error) {
      console.error('Upload failed:', error);

      // Update progress to error for all files
      fileIds.forEach(fileId => {
        setUploadProgress(prev => ({
          ...prev,
          [fileId]: {
            status: 'error',
            progress: 0,
            error: error.message || 'Upload failed'
          }
        }));
      });

    } finally {
      // Remove from uploading state after a delay
      setTimeout(() => {
        setUploadingFiles(prev => {
          const newSet = new Set(prev);
          fileIds.forEach(id => newSet.delete(id));
          return newSet;
        });
      }, 2000);
    }
  };

  // Resize handlers
  const handleMouseDownLeft = (e) => {
    setIsResizingLeft(true);
    e.preventDefault();
  };

  const handleMouseDownRight = (e) => {
    setIsResizingRight(true);
    e.preventDefault();
  };

  const handleMouseMove = (e) => {
    if (!containerRef.current) return;

    const containerRect = containerRef.current.getBoundingClientRect();
    const screenWidth = window.innerWidth;

    // Responsive resize limits
    let minWidth, maxWidth;
    if (screenWidth < 640) {
      minWidth = 150;
      maxWidth = 250;
    } else if (screenWidth < 1024) {
      minWidth = 180;
      maxWidth = 350;
    } else {
      minWidth = 200;
      maxWidth = 500;
    }

    if (isResizingLeft) {
      const newWidth = Math.max(minWidth, Math.min(maxWidth, e.clientX - containerRect.left));
      setLeftPanelWidth(newWidth);
    } else if (isResizingRight) {
      const newWidth = Math.max(minWidth, Math.min(maxWidth, containerRect.right - e.clientX));
      setRightPanelWidth(newWidth);
    }
  };

  const handleMouseUp = () => {
    setIsResizingLeft(false);
    setIsResizingRight(false);
  };

  // Add global mouse event listeners when resizing
  React.useEffect(() => {
    if (isResizingLeft || isResizingRight) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'col-resize';
      document.body.style.userSelect = 'none';
      document.body.classList.add('resizing');
    } else {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.body.classList.remove('resizing');
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = '';
      document.body.style.userSelect = '';
      document.body.classList.remove('resizing');
    };
  }, [isResizingLeft, isResizingRight]);

  // Chat History Functions
  const saveCurrentChat = () => {
    if (messages.length > 0 && pageName.trim()) {
      const chatSession = {
        id: currentChatId || Date.now(),
        name: pageName,
        messages: [...messages],
        timestamp: new Date(),
        sources: sources.length,
      };

      setChatHistory(prev => {
        const existingIndex = prev.findIndex(chat => chat.id === chatSession.id);
        if (existingIndex >= 0) {
          // Update existing chat
          const updated = [...prev];
          updated[existingIndex] = chatSession;
          return updated;
        } else {
          // Add new chat
          return [chatSession, ...prev];
        }
      });

      setCurrentChatId(chatSession.id);
    }
  };

  const loadChat = (chatId) => {
    const chat = chatHistory.find(c => c.id === chatId);
    if (chat) {
      setPageName(chat.name);
      setMessages(chat.messages);
      setCurrentChatId(chat.id);
    }
  };

  const createNewChat = () => {
    // Save current chat if it has messages
    if (messages.length > 0) {
      saveCurrentChat();
    }

    // Reset to new chat
    setPageName('Untitled Planet');
    setMessages([]);
    setCurrentChatId(null);
    setEvidenceData(null);
  };

  // Auto-save chat when page name changes
  React.useEffect(() => {
    if (messages.length > 0) {
      saveCurrentChat();
    }
  }, [pageName]);

  const handleRenameSave = () => {
    const trimmedName = newPlanetName.trim();
    if (!trimmedName) {
      setRenameError('Planet name cannot be empty');
      return;
    }

    // Check for duplicate names
    const planetHistory = JSON.parse(localStorage.getItem('planetHistory') || '[]');
    const existingPlanet = planetHistory.find(planet => planet.name === trimmedName);
    if (existingPlanet) {
      setRenameError('A planet with this name already exists. Please choose a different name.');
      return;
    }

    // Save the new planet
    setPageName(trimmedName);
    setCurrentChatId(Date.now());
    setShowRenameModal(false);
    setRenameError('');
    
    // Navigate based on exit action
    if (exitAction === 'back') {
      window.history.back();
    } else if (exitAction === 'newplanet') {
      navigate('/newplanet');
    }
    setExitAction('back'); // Reset
  };

  const handleRenameCancel = () => {
    setShowRenameModal(false);
    setNewPlanetName('Untitled Planet');
    setRenameError('');
  };

  const handlePageNameChange = (newName) => {
    const oldName = pageName;
    setPageName(newName);

    // Update planet history if name changed
    if (newName.trim() && newName !== oldName) {
      const planetHistory = JSON.parse(localStorage.getItem('planetHistory') || '[]');
      const planetData = {
        id: currentChatId,
        name: newName,
        messages: messages,
        timestamp: new Date().toISOString(),
        sources: sources.length,
      };

      // Update existing planet
      const existingIndex = planetHistory.findIndex(p => p.id === currentChatId);
      if (existingIndex >= 0) {
        planetHistory[existingIndex] = planetData;
      }

      localStorage.setItem('planetHistory', JSON.stringify(planetHistory));
    }
  };

  const handleBack = () => {
    // Check if this planet exists in history
    const planetHistory = JSON.parse(localStorage.getItem('planetHistory') || '[]');
    const existingPlanet = planetHistory.find(planet => planet.id === currentChatId);

    // If planet exists in history, just go back
    if (existingPlanet) {
      window.history.back();
      return;
    }

    // If new planet and has messages, show exit prompt
    if (messages.length > 0) {
      setShowExitPrompt(true);
      setExitAction('back');
    } else {
      // No messages, just go back
      window.history.back();
    }
  };

  const handleExitDiscard = () => {
    setShowExitPrompt(false);
    if (exitAction === 'back') {
      window.history.back();
    } else if (exitAction === 'newplanet') {
      navigate('/newplanet');
    }
    setExitAction('back'); // Reset
  };

  const handleExitRename = () => {
    setShowExitPrompt(false);
    setShowRenameModal(true);
  };

  const handleNewPlanet = () => {
    // Check if this planet exists in history
    const planetHistory = JSON.parse(localStorage.getItem('planetHistory') || '[]');
    const existingPlanet = planetHistory.find(planet => planet.id === currentChatId);

    // If planet exists in history, just navigate to new planet
    if (existingPlanet) {
      navigate('/newplanet');
      return;
    }

    // If new planet and has messages, show exit prompt
    if (messages.length > 0) {
      setShowExitPrompt(true);
      setExitAction('newplanet'); // Flag to know what action to take after saving
    } else {
      // No messages, just go to new planet
      navigate('/newplanet');
    }
  };

  return (
    <div className="h-screen bg-[var(--bg-color,#000000)] dark:bg-[var(--bg-color,#000000)] transition-colors duration-300 overflow-hidden">
      {/* Fixed Desktop Canvas */}
      <div className="w-full h-full flex flex-col dashboard-container">
        
        {/* Header */}
        <Header user={user} onBack={handleBack} onNewPlanet={handleNewPlanet} />

        <div ref={containerRef} className="flex-1 flex overflow-hidden relative panel-layout h-full">
          
          {/* Left Panel - Sources */}
          {leftPanelOpen && (
            <>
              <LeftPanel 
                sources={sources}
                onFileUpload={handleFileUpload}
                isLoading={sourcesLoading}
                width={leftPanelWidth}
                uploadProgress={uploadProgress}
                uploadingFiles={uploadingFiles}
                chatHistory={chatHistory}
                onLoadChat={loadChat}
                onNewChat={createNewChat}
                onTogglePanel={() => setLeftPanelOpen(!leftPanelOpen)}
              />
              
              {/* Left Resize Handle */}
              {!isMobile && (
                <div
                  className={`resize-handle ${isResizingLeft ? 'active' : ''}`}
                  onMouseDown={handleMouseDownLeft}
                >
                  <div className="resize-handle-button"></div>
                </div>
              )}
            </>
          )}

          {/* Left Panel Toggle Button - When closed */}
          {!leftPanelOpen && (
            <button
              onClick={() => setLeftPanelOpen(!leftPanelOpen)}
              className="absolute left-2 top-20 z-30 p-2 rounded-r-lg bg-[var(--card-bg,#14141f)] hover:bg-[var(--card-bg,#14141f)]/80 border border-[var(--card-border,#1f1f2e)] transition-all duration-200 shadow-sm"
              aria-label="Toggle sources panel"
            >
              <svg className="w-4 h-4 text-[var(--secondary-text,#9ca3af)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </button>
          )}

          {/* Center Panel - Main Workspace */}
          <CenterPanel 
            messages={messages}
            onSendMessage={handleSendMessage}
            leftPanelOpen={leftPanelOpen}
            rightPanelOpen={rightPanelOpen}
            isLoading={messagesLoading}
            pageName={pageName}
            onPageNameChange={handlePageNameChange}
            isMobile={isMobile}
          />

          {/* Right Panel - Evidence */}
          {rightPanelOpen && (
            <>
              {/* Right Resize Handle */}
              {!isMobile && (
                <div
                  className={`resize-handle ${isResizingRight ? 'active' : ''}`}
                  onMouseDown={handleMouseDownRight}
                >
                  <div className="resize-handle-button"></div>
                </div>
              )}
              
              <RightPanel 
                evidenceData={evidenceData}
                isLoading={evidenceLoading}
                width={rightPanelWidth}
                onTogglePanel={() => setRightPanelOpen(!rightPanelOpen)}
              />
            </>
          )}

          {/* Right Panel Toggle Button - When closed */}
          {!rightPanelOpen && (
            <button
              onClick={() => setRightPanelOpen(!rightPanelOpen)}
              className="absolute right-2 top-20 z-30 p-2 rounded-l-lg bg-[var(--card-bg,#14141f)] hover:bg-[var(--card-bg,#14141f)]/80 border border-[var(--card-border,#1f1f2e)] transition-all duration-200 shadow-sm"
              aria-label="Toggle analysis panel"
            >
              <svg className="w-4 h-4 text-[var(--secondary-text,#9ca3af)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
            </button>
          )}

        </div>

        {/* Rename Modal */}
        {showRenameModal && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-[var(--card-bg,#ffffff)] dark:bg-[var(--card-bg,#2a2a30)] border border-[var(--card-border,#e5e7eb)] dark:border-[var(--card-border,#3a3a3c)] rounded-lg shadow-lg max-w-md w-full">
              <div className="p-6">
                <h2 className="text-xl font-semibold mb-4 text-[var(--text-color,#000000)] dark:text-[var(--text-color,#ffffff)]">Name Your New Planet</h2>
                <input
                  type="text"
                  value={newPlanetName}
                  onChange={(e) => setNewPlanetName(e.target.value)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter') handleRenameSave();
                    if (e.key === 'Escape') handleRenameCancel();
                  }}
                  className="w-full px-3 py-2 border border-[var(--card-border,#e5e7eb)] dark:border-[var(--card-border,#3a3a3c)] rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 bg-[var(--bg-color,#ffffff)] dark:bg-[var(--bg-color,#1b1b1d)] text-[var(--text-color,#000000)] dark:text-[var(--text-color,#ffffff)] placeholder-[var(--secondary-text,#6b7280)] dark:placeholder-[var(--secondary-text,#d1d5db)]"
                  placeholder="Enter planet name"
                  autoFocus
                />
                {renameError && (
                  <p className="text-red-500 text-sm mt-2">{renameError}</p>
                )}
                <div className="flex justify-end gap-3 mt-4">
                  <button
                    onClick={handleRenameCancel}
                    className="px-4 py-2 text-[var(--secondary-text,#6b7280)] dark:text-[var(--secondary-text,#d1d5db)] hover:bg-[var(--card-bg,#f9fafb)] dark:hover:bg-[var(--card-bg,#2a2a30)] rounded-md transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleRenameSave}
                    className="px-4 py-2 bg-blue-500 text-white hover:bg-blue-600 rounded-md disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                    disabled={!newPlanetName.trim()}
                  >
                    Save
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Exit Prompt Modal */}
        {showExitPrompt && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-[var(--card-bg,#ffffff)] dark:bg-[var(--card-bg,#2a2a30)] border border-[var(--card-border,#e5e7eb)] dark:border-[var(--card-border,#3a3a3c)] rounded-lg shadow-lg max-w-md w-full">
              <div className="p-6">
                <h2 className="text-xl font-semibold mb-4 text-[var(--text-color,#000000)] dark:text-[var(--text-color,#ffffff)]">
                  {exitAction === 'back' ? 'Save Your Work?' : 'Save Before Creating New Planet?'}
                </h2>
                <p className="text-[var(--secondary-text,#6b7280)] dark:text-[var(--secondary-text,#d1d5db)] mb-6">
                  You have unsaved changes. Would you like to save your planet {exitAction === 'back' ? 'before leaving' : 'before creating a new one'}?
                </p>
                <div className="flex justify-end gap-3">
                  <button
                    onClick={handleExitDiscard}
                    className="px-4 py-2 text-[var(--secondary-text,#6b7280)] dark:text-[var(--secondary-text,#d1d5db)] hover:bg-[var(--card-bg,#f9fafb)] dark:hover:bg-[var(--card-bg,#2a2a30)] rounded-md transition-colors"
                  >
                    {exitAction === 'back' ? 'Discard' : "Don't Save"}
                  </button>
                  <button
                    onClick={handleExitRename}
                    className="px-4 py-2 bg-blue-500 text-white hover:bg-blue-600 rounded-md transition-colors"
                  >
                    {exitAction === 'back' ? 'Save & Exit' : 'Save & Continue'}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
