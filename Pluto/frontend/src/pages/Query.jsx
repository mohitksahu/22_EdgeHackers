import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import QueryInput from '../components/query/QueryInput';
import ModalityFilter from '../components/query/ModalityFilter';
import ChatHistory from '../components/query/ChatHistory';
import SessionManager from '../components/system/SessionManager';
import { submitQuery } from '../services/queryService';
import { switchToPlanet } from '../services/sessionService';

function Query() {
  const [query, setQuery] = useState('');
  const [selectedModalities, setSelectedModalities] = useState(['text', 'image', 'audio']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!query.trim()) {
      setError('Please enter a query');
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // Submit query to backend
      const results = await submitQuery(query);
      
      // Navigate to results page with query data and results
      navigate('/results', { 
        state: { 
          query, 
          modalities: selectedModalities,
          results 
        } 
      });
    } catch (err) {
      setError('Failed to submit query. Please try again.');
      console.error('Query submission error:', err);
    } finally {
      setLoading(false);
    }
  };

  const handlePlanetClick = (planet) => {
    switchToPlanet(planet.id); // Sets active session
    navigate("/dashboard", { state: { loadPlanet: planet } });
  };

  return (
    <div className="min-h-screen bg-[var(--bg-color,#000000)] text-[var(--text-color,#ffffff)] p-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-[var(--text-color,#ffffff)] mb-6">Query the System</h1>
        
        {/* Session Manager */}
        <SessionManager />
        
        {/* Chat History */}
        <ChatHistory />
        
        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-3 rounded mb-4">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-6">
          <QueryInput value={query} onChange={setQuery} />
          <ModalityFilter
            selected={selectedModalities}
            onChange={setSelectedModalities}
          />
          <button 
            type="submit" 
            className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
            disabled={loading || !query.trim()}
          >
            {loading ? 'Processing...' : 'Submit Query'}
          </button>
        </form>
      </div>
    </div>
  );
}

export default Query;
