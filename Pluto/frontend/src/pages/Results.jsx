import { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import EvidencePanel from '../components/evidence/EvidencePanel';
import GeneratedResponse from '../components/response/GeneratedResponse';

function Results() {
  const location = useLocation();
  const navigate = useNavigate();
  const { query, modalities, results: initialResults } = location.state || {};
  const [results, setResults] = useState(initialResults);

  useEffect(() => {
    // If no query or results, redirect to query page
    if (!query || !results) {
      navigate('/query');
    }
  }, [query, results, navigate]);

  if (!results) {
    return null;
  }

  // Map backend response to frontend component expectations
  const responseData = {
    content: results.response,
    refusal: results.refusal,
    confidence: results.confidence_score,
    citations: results.cited_sources || [],
    conflicts: results.conflicts || [],
    assumptions: results.assumptions || [],
    processingTime: results.processing_time
  };

  // Map cited sources to evidence format
  const evidenceData = (results.cited_sources || []).map((source, index) => ({
    id: index,
    modality: source.modality || 'text',
    content: source.content || source.text || '',
    confidence: source.score || source.confidence || 0,
    source: {
      filename: source.filename || source.source || 'Unknown',
      page: source.page,
      timestamp: source.timestamp
    }
  }));

  return (
    <div className="min-h-screen bg-[var(--bg-color,#000000)] text-[var(--text-color,#ffffff)] p-4 py-8">
      <div className="max-w-6xl mx-auto space-y-8">
        <div>
          <h1 className="text-3xl font-bold text-[var(--text-color,#ffffff)] mb-2">Query Results</h1>
          <p className="text-gray-400 text-sm">Query: "{query}"</p>
          {results.processing_time && (
            <p className="text-gray-500 text-xs mt-1">
              Processing time: {results.processing_time.toFixed(2)}s
            </p>
          )}
        </div>
        
        <GeneratedResponse response={responseData} />
        <EvidencePanel evidence={evidenceData} />
        
        <button
          onClick={() => navigate('/query')}
          className="btn-primary mt-4"
        >
          New Query
        </button>
      </div>
    </div>
  );
}

export default Results;
