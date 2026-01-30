import { useState, useRef } from 'react';

export default function LeftPanel({ sources, onFileUpload, isLoading, width = 260, uploadProgress = {}, uploadingFiles = new Set(), chatHistory = [], onLoadChat, onNewChat, onTogglePanel }) {
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef(null);

  const handleDragOver = (e) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = () => {
    setIsDragging(false);
  };

  const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg', '.mp3', '.wav'];

  const validateFiles = (fileList) => {
    const invalidFiles = [];
    Array.from(fileList).forEach(file => {
      const extension = '.' + file.name.split('.').pop().toLowerCase();
      if (!ALLOWED_EXTENSIONS.includes(extension)) {
        invalidFiles.push(file.name);
      }
    });
    return invalidFiles;
  };

  const handleDrop = (e) => {
    e.preventDefault();
    setIsDragging(false);
    const files = e.dataTransfer.files;
    if (files.length > 0) {
      // Validate files before upload
      const invalidFiles = validateFiles(files);
      if (invalidFiles.length > 0) {
        alert(`Unsupported file type(s): ${invalidFiles.join(', ')}\n\nOnly PDF, DOC, DOCX, TXT, PNG, JPG, JPEG, MP3, and WAV files are allowed.`);
        return;
      }
      onFileUpload(files);
    }
  };

  const handleFileSelect = (e) => {
    const files = e.target.files;
    if (files.length > 0) {
      // Validate files before upload
      const invalidFiles = validateFiles(files);
      if (invalidFiles.length > 0) {
        alert(`Unsupported file type(s): ${invalidFiles.join(', ')}\n\nOnly PDF, DOC, DOCX, TXT, PNG, JPG, JPEG, MP3, and WAV files are allowed.`);
        e.target.value = ''; // Clear input
        return;
      }
      onFileUpload(files);
    }
  };

  const getFileIcon = (type) => {
    if (type === 'pdf') {
      return (
        <svg className="w-5 h-5 text-red-400" fill="currentColor" viewBox="0 0 20 20">
          <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
        </svg>
      );
    }
    return (
      <svg className="w-5 h-5 text-blue-400" fill="currentColor" viewBox="0 0 20 20">
        <path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4zm2 6a1 1 0 011-1h6a1 1 0 110 2H7a1 1 0 01-1-1zm1 3a1 1 0 100 2h6a1 1 0 100-2H7z" clipRule="evenodd" />
      </svg>
    );
  };

  return (
    <aside className="flex-shrink-0 border-r border-t border-[var(--card-border,#1f1f2e)] flex flex-col md:relative absolute inset-y-0 left-0 z-20 bg-[var(--bg-color,#000000)] overflow-y-auto h-full" style={{ width: `${width}px` }}>
      {/* Panel Header */}
      <div className="panel-header flex items-center justify-between px-6 py-4">
        <button
          onClick={onTogglePanel}
          className="p-2 rounded-lg bg-[var(--card-bg,#14141f)] hover:bg-[var(--card-bg,#14141f)]/80 border border-[var(--card-border,#1f1f2e)] transition-all duration-200 shadow-sm"
          aria-label="Toggle sources panel"
        >
          <svg className="w-4 h-4 text-[var(--secondary-text,#9ca3af)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
        </button>
        <h2 className="text-base font-medium text-white text-center flex-1">Sources</h2>
      </div>

      {/* Chat History Section */}
      {chatHistory.length > 0 && (
        <div className="border-b border-[var(--card-border,#1f1f2e)]">
          <div className="px-6 py-3">
            <h3 className="text-sm font-medium text-[var(--secondary-text,#9ca3af)] uppercase tracking-wide">
              Chat History
            </h3>
          </div>
          <div className="px-3 pb-3 space-y-1 max-h-48 overflow-y-auto">
            {chatHistory.slice(0, 10).map((chat) => (
              <button
                key={chat.id}
                onClick={() => onLoadChat(chat.id)}
                className="w-full text-left p-2 rounded-lg hover:bg-[var(--card-bg,#14141f)]/50 transition-colors group"
              >
                <div className="flex items-center justify-between">
                  <span className="text-sm text-[var(--text-color)] truncate block">
                    {chat.name}
                  </span>
                  <span className="text-xs text-[var(--secondary-text,#9ca3af)] opacity-0 group-hover:opacity-100 transition-opacity">
                    {chat.messages.length} msgs
                  </span>
                </div>
                <div className="text-xs text-[var(--secondary-text,#9ca3af)] mt-1">
                  {new Date(chat.timestamp).toLocaleDateString()}
                </div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Combined Upload and Sources Area - Single Scrollable Container */}
      <div className="flex-1 overflow-y-auto">
        {/* Upload Area */}
        <div className="p-6">
          <input
            ref={fileInputRef}
            type="file"
            multiple
            className="hidden"
            onChange={handleFileSelect}
            accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.mp3,.wav"
          />
          
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => fileInputRef.current?.click()}
            className={`
              border-2 border-dashed rounded-xl p-6 cursor-pointer
              transition-all duration-200
              ${isDragging 
                ? 'border-pluto-purple bg-pluto-purple/5' 
                : 'border-[var(--card-border,#1f1f2e)] hover:border-[var(--secondary-text,#9ca3af)] hover:bg-[var(--card-bg,#14141f)]/50'
              }
            `}
          >
            <div className="flex flex-col items-center text-center gap-2">
              <svg className="w-8 h-8 text-[var(--secondary-text,#9ca3af)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
              </svg>
              <div className="text-sm text-[var(--secondary-text,#9ca3af)]">
                <span className="text-pluto-purple font-medium">Upload files</span>
                <br />or drag and drop
              </div>
              <div className="text-xs text-[var(--secondary-text,#9ca3af)] mt-1">
                PDF, DOC, DOCX, TXT, PNG, JPG, JPEG, MP3, WAV
              </div>
            </div>
          </div>
        </div>

        {/* Sources List */}
        <div className="px-6 pb-6 space-y-2">
        {/* Uploading Files Section */}
        {Array.from(uploadingFiles).length > 0 && (
          <div className="mb-4">
            <h3 className="text-xs font-medium text-[var(--secondary-text,#9ca3af)] uppercase tracking-wider mb-3">
              Uploading
            </h3>
            <div className="space-y-2">
              {Array.from(uploadingFiles).map((fileId) => {
                const progress = uploadProgress[fileId];
                const fileName = fileId.split('-').slice(0, -1).join('-'); // Remove timestamp
                
                return (
                  <div
                    key={fileId}
                    className="p-3 rounded-xl bg-[var(--card-bg,#14141f)]/50 border border-[var(--card-border,#1f1f2e)]"
                  >
                    <div className="flex items-start gap-3 mb-2">
                      {progress?.status === 'error' ? (
                        <svg className="w-5 h-5 text-red-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                        </svg>
                      ) : progress?.status === 'completed' ? (
                        <svg className="w-5 h-5 text-green-400 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                      ) : (
                        <div className="w-5 h-5 border-2 border-pluto-purple border-t-transparent rounded-full animate-spin flex-shrink-0 mt-0.5"></div>
                      )}
                      <div className="flex-1 min-w-0">
                        <p className="text-sm text-white font-medium truncate leading-tight">
                          {fileName}
                        </p>
                        <p className="text-xs text-[var(--secondary-text,#9ca3af)] mt-1">
                          {progress?.status === 'error' ? progress.error :
                           progress?.status === 'completed' ? 'Upload complete' :
                           progress?.status === 'processing' ? 'Processing...' : 'Uploading...'}
                        </p>
                      </div>
                    </div>
                    
                    {/* Progress Bar */}
                    {progress?.status !== 'error' && (
                      <div className="mt-2">
                        <div className="h-1 bg-[var(--card-border,#1f1f2e)] rounded-full overflow-hidden">
                          <div
                            className="h-full bg-gradient-to-r from-pluto-purple to-pluto-purple-light rounded-full transition-all duration-300"
                            style={{ width: `${progress?.progress || 0}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* Uploaded Sources Section */}
        <div>
          <h3 className="text-xs font-medium text-[var(--secondary-text,#9ca3af)] uppercase tracking-wider mb-3">
            Sources ({sources.length})
          </h3>
          {isLoading ? (
            /* Loading Skeleton */
            <>
              {[1, 2, 3].map((i) => (
                <div
                  key={i}
                  className="p-3 rounded-xl bg-[var(--card-bg,#14141f)]/50 border border-[var(--card-border,#1f1f2e)]"
                >
                  <div className="flex items-start gap-3">
                    <div className="w-5 h-5 bg-[var(--card-border,#1f1f2e)] rounded animate-pulse-slow flex-shrink-0"></div>
                    <div className="flex-1 space-y-2">
                      <div className="h-4 bg-[var(--card-border,#1f1f2e)] rounded animate-pulse-slow w-3/4"></div>
                      <div className="h-3 bg-[var(--card-border,#1f1f2e)] rounded animate-pulse-slow w-1/2"></div>
                    </div>
                  </div>
                </div>
              ))}
            </>
          ) : sources.length === 0 ? (
            /* Empty State */
            <div className="flex items-center justify-center py-12">
              <div className="text-center max-w-xs px-4">
                <div className="mb-4 flex justify-center">
                  <svg className="w-12 h-12 text-[var(--secondary-text,#9ca3af)] opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
                  </svg>
                </div>
                <p className="text-sm text-[var(--secondary-text,#9ca3af)] leading-relaxed">
                  No sources added yet. Uploaded documents will appear here.
                </p>
              </div>
            </div>
          ) : (
            /* Source Cards with Data */
            sources.map((source) => (
              <div
                key={source.id}
                className="group p-3 rounded-xl bg-[var(--card-bg,#14141f)]/50 hover:bg-[var(--card-bg,#14141f)] border border-[var(--card-border,#1f1f2e)] hover:border-[var(--secondary-text,#9ca3af)]/20 cursor-pointer transition-all duration-200 hover:shadow-lg"
              >
                <div className="flex items-start gap-3">
                  {getFileIcon(source.type)}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="text-sm text-white font-medium truncate leading-tight">
                        {source.name}
                      </p>
                      {source.modality && (
                        <span className="text-xs px-2 py-0.5 rounded-full bg-pluto-purple/20 text-pluto-purple border border-pluto-purple/30">
                          {source.modality}
                        </span>
                      )}
                    </div>

                    <div className="flex items-center justify-between text-xs text-[var(--secondary-text,#9ca3af)]">
                      <span>{source.timestamp}</span>
                      {source.chunks && (
                        <span>{source.chunks} chunks</span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>
        </div>
      </div>
    </aside>
  );
}
