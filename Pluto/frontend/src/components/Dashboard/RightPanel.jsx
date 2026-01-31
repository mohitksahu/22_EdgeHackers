export default function RightPanel({ evidenceData, isLoading, width = 300, onTogglePanel }) {
  const hasEvidence = evidenceData && evidenceData.cards && evidenceData.cards.length > 0;

  return (
    <aside className="flex-shrink-0 border-l border-t border-[var(--card-border,#1f1f2e)] flex flex-col md:relative absolute inset-y-0 right-0 z-20 bg-[var(--bg-color,#000000)] overflow-y-auto h-full" style={{ width: `${width}px` }}>
      {/* Panel Header with Confidence */}
      <div className="panel-header flex items-center justify-between px-6 py-4">
        <h2 className="text-base font-medium text-white">Analysis</h2>
        <button
          onClick={onTogglePanel}
          className="p-2 rounded-lg bg-[var(--card-bg,#14141f)] hover:bg-[var(--card-bg,#14141f)]/80 border border-[var(--card-border,#1f1f2e)] transition-all duration-200 shadow-sm"
          aria-label="Toggle analysis panel"
        >
          <svg className="w-4 h-4 text-[var(--secondary-text,#9ca3af)]" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* Confidence Indicator - Only show when there's evidence */}
      {isLoading ? (
        <div className="px-6 mb-6 mt-6">
          <div className="p-5 rounded-2xl bg-[var(--card-bg,#14141f)]/50 border border-[var(--card-border,#1f1f2e)]">
            <div className="flex items-center gap-4">
              {/* Skeleton Circular Progress */}
              <div className="relative w-16 h-16 flex-shrink-0">
                <svg className="w-16 h-16 transform -rotate-90">
                  <circle
                    cx="32"
                    cy="32"
                    r="28"
                    stroke="currentColor"
                    strokeWidth="6"
                    fill="none"
                    className="text-[var(--card-border,#1f1f2e)] animate-pulse-slow"
                  />
                </svg>
              </div>
              {/* Skeleton Text */}
              <div className="flex-1 space-y-2">
                <div className="h-4 bg-[var(--card-border,#1f1f2e)] rounded animate-pulse-slow w-3/4"></div>
                <div className="h-3 bg-[var(--card-border,#1f1f2e)] rounded animate-pulse-slow w-1/2"></div>
              </div>
            </div>
          </div>
        </div>
      ) : hasEvidence && evidenceData.confidence !== undefined ? (
        <>
          {/* Conflict Warning - Show if conflicts detected */}
          {evidenceData.conflictsDetected && (
            <div className="px-6 mb-4 mt-6">
              <div className="p-4 rounded-xl bg-yellow-500/10 border border-yellow-500/30">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-yellow-500 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                  </svg>
                  <div className="flex-1">
                    <p className="text-sm font-medium text-yellow-500 mb-1">Conflicting Information</p>
                    <p className="text-xs text-yellow-500/80">Multiple sources contain contradictory data. Review evidence carefully.</p>
                  </div>
                </div>
              </div>
            </div>
          )}
          
          <div className="px-6 mb-6 mt-6">
            <div className="p-5 rounded-2xl bg-[var(--card-bg,#14141f)]/50 border border-[var(--card-border,#1f1f2e)]">
              <div className="flex items-center gap-4">
                {/* Circular Progress */}
                <div className="relative w-16 h-16 flex-shrink-0">
                  <svg className="w-16 h-16 transform -rotate-90">
                    <circle
                      cx="32"
                      cy="32"
                      r="28"
                      stroke="currentColor"
                      strokeWidth="6"
                      fill="none"
                      className="text-[var(--card-border,#1f1f2e)]"
                    />
                    <circle
                      cx="32"
                      cy="32"
                      r="28"
                      stroke="currentColor"
                      strokeWidth="6"
                      fill="none"
                      strokeDasharray={`${2 * Math.PI * 28}`}
                      strokeDashoffset={`${2 * Math.PI * 28 * (1 - evidenceData.confidence / 100)}`}
                      className="text-pluto-purple transition-all duration-1000"
                      strokeLinecap="round"
                    />
                  </svg>
                  <div className="absolute inset-0 flex items-center justify-center">
                    <span className="text-sm font-semibold text-white">{evidenceData.confidence}%</span>
                  </div>
                </div>

                {/* Text */}
                <div className="flex-1">
                  <p className="text-sm font-medium text-white mb-1">
                    {evidenceData.confidence >= 80 ? 'High Confidence' : evidenceData.confidence >= 60 ? 'Moderate Confidence' : 'Low Confidence'}
                  </p>
                  <p className="text-xs text-[var(--secondary-text,#9ca3af)]">
                    {evidenceData.confidence >= 80 ? 'Strong evidence alignment' : evidenceData.confidence >= 60 ? 'Moderate evidence support' : 'Limited evidence available'}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </>
      ) : null}

      {/* Evidence Sources Header - Positioned at top center */}
      <div className="px-6 py-3 border-b border-[var(--card-border,#1f1f2e)]">
        <h3 className="text-xs font-medium text-[var(--secondary-text,#9ca3af)] uppercase tracking-wider text-center">
          Evidence Sources
        </h3>
      </div>

      {/* Evidence Cards */}
      <div className="flex-1 overflow-y-auto px-6 space-y-3 pb-6">
        
        {isLoading ? (
          /* Loading Skeleton */
          <>
            {[1, 2].map((i) => (
              <div
                key={i}
                className="p-4 rounded-xl bg-[var(--card-bg,#14141f)]/50 border border-[var(--card-border,#1f1f2e)]"
              >
                <div className="flex items-start gap-3 mb-3">
                  <div className="w-5 h-5 bg-[var(--card-border,#1f1f2e)] rounded animate-pulse-slow flex-shrink-0"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 bg-[var(--card-border,#1f1f2e)] rounded animate-pulse-slow w-3/4"></div>
                    <div className="h-3 bg-[var(--card-border,#1f1f2e)] rounded animate-pulse-slow w-1/2"></div>
                  </div>
                </div>
                <div className="mb-3">
                  <div className="h-3 bg-[var(--card-border,#1f1f2e)] rounded animate-pulse-slow mb-1.5"></div>
                  <div className="h-1.5 bg-[var(--card-border,#1f1f2e)] rounded-full animate-pulse-slow"></div>
                </div>
                <div className="h-3 bg-[var(--card-border,#1f1f2e)] rounded animate-pulse-slow"></div>
              </div>
            ))}
          </>
        ) : !hasEvidence ? (
          /* Empty State */
          <div className="flex items-center justify-center py-12">
            <div className="text-center max-w-xs">
              <div className="mb-4 flex justify-center">
                <svg className="w-12 h-12 text-[var(--secondary-text,#9ca3af)] opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <p className="text-sm text-[var(--secondary-text,#9ca3af)] leading-relaxed">
                No evidence available yet. Evidence will appear here after a query is processed.
              </p>
            </div>
          </div>
        ) : (
          /* Evidence Cards with Data */
          evidenceData.cards.map((card) => (
            <div
              key={card.id}
              className="group p-4 rounded-xl bg-[var(--card-bg,#14141f)]/50 hover:bg-[var(--card-bg,#14141f)] border border-[var(--card-border,#1f1f2e)] hover:border-[var(--secondary-text,#9ca3af)]/20 cursor-pointer transition-all duration-200"
            >
              {/* File Info */}
              <div className="flex items-start gap-3 mb-3">
                <svg className="w-5 h-5 text-pluto-purple flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                </svg>
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white font-medium truncate leading-tight">
                    {card.filename}
                  </p>
                  <p className="text-xs text-[var(--secondary-text,#9ca3af)] mt-1">
                    {card.timestamp}
                  </p>
                </div>
              </div>

              {/* Confidence Bar */}
              {card.confidence !== undefined && (
                <div className="mb-3">
                  <div className="flex items-center justify-between mb-1.5">
                    <span className="text-xs text-[var(--secondary-text,#9ca3af)]">Confidence</span>
                    <span className="text-xs font-medium text-pluto-purple">{card.confidence}%</span>
                  </div>
                  <div className="h-1.5 bg-[var(--card-border,#1f1f2e)] rounded-full overflow-hidden">
                    <div
                      className="h-full bg-gradient-to-r from-pluto-purple to-pluto-purple-light rounded-full transition-all duration-500"
                      style={{ width: `${card.confidence}%` }}
                    />
                  </div>
                </div>
              )}

              {/* Excerpt */}
              {card.excerpt && (
                <p className="text-xs text-[var(--secondary-text,#9ca3af)] leading-relaxed line-clamp-2">
                  {card.excerpt}
                </p>
              )}
            </div>
          ))
        )}
      </div>

      {/* Footer Summary */}
      {hasEvidence && evidenceData.sources !== undefined && (
        <div className="p-6 border-t border-[var(--card-border,#1f1f2e)]">
          <div className="flex items-center justify-between text-sm">
            <span className="text-[var(--secondary-text,#9ca3af)]">Sources used</span>
            <span className="font-medium text-white">{evidenceData.sources}</span>
          </div>
        </div>
      )}

    </aside>
  );
}
