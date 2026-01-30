import { useState } from 'react';
import { checkHealth } from '../services/api';
import { checkQueryHealth } from '../services/queryService';
import { getVectorStoreStats } from '../services/retrievalService';

/**
 * ConnectionTest Component
 * Simple component to test backend connectivity
 * Use this during development to verify the frontend-backend connection
 */
function ConnectionTest() {
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(false);

  const runTests = async () => {
    setLoading(true);
    const testResults = {};

    // Test 1: Health endpoint
    try {
      const health = await checkHealth();
      testResults.health = { status: 'success', data: health };
    } catch (error) {
      testResults.health = { status: 'error', error: error.message };
    }

    // Test 2: Query health
    try {
      const queryHealth = await checkQueryHealth();
      testResults.queryHealth = { status: 'success', data: queryHealth };
    } catch (error) {
      testResults.queryHealth = { status: 'error', error: error.message };
    }

    // Test 3: Vector store stats
    try {
      const stats = await getVectorStoreStats();
      testResults.vectorStats = { status: 'success', data: stats };
    } catch (error) {
      testResults.vectorStats = { status: 'error', error: error.message };
    }

    setResults(testResults);
    setLoading(false);
  };

  return (
    <div style={{ padding: '20px', maxWidth: '800px', margin: '0 auto' }}>
      <h1>Backend Connection Test</h1>
      <button 
        onClick={runTests} 
        disabled={loading}
        style={{
          padding: '10px 20px',
          backgroundColor: '#4F46E5',
          color: 'white',
          border: 'none',
          borderRadius: '4px',
          cursor: loading ? 'not-allowed' : 'pointer',
          marginBottom: '20px'
        }}
      >
        {loading ? 'Testing...' : 'Run Connection Tests'}
      </button>

      {Object.keys(results).length > 0 && (
        <div>
          <h2>Test Results:</h2>
          {Object.entries(results).map(([test, result]) => (
            <div 
              key={test}
              style={{
                padding: '15px',
                marginBottom: '10px',
                borderRadius: '4px',
                backgroundColor: result.status === 'success' ? '#D1FAE5' : '#FEE2E2',
                border: `1px solid ${result.status === 'success' ? '#10B981' : '#EF4444'}`
              }}
            >
              <h3>{test}</h3>
              <p><strong>Status:</strong> {result.status}</p>
              {result.data && (
                <pre style={{ 
                  backgroundColor: '#F3F4F6', 
                  padding: '10px', 
                  borderRadius: '4px',
                  overflow: 'auto'
                }}>
                  {JSON.stringify(result.data, null, 2)}
                </pre>
              )}
              {result.error && (
                <p style={{ color: '#DC2626' }}><strong>Error:</strong> {result.error}</p>
              )}
            </div>
          ))}
        </div>
      )}

      <div style={{ marginTop: '40px', padding: '15px', backgroundColor: '#F3F4F6', borderRadius: '4px' }}>
        <h3>What's being tested:</h3>
        <ul>
          <li><strong>Health:</strong> GET /health - Basic server health check</li>
          <li><strong>Query Health:</strong> GET /api/v1/query/health - Query service status</li>
          <li><strong>Vector Stats:</strong> GET /api/v1/vector/stats - Vector store statistics</li>
        </ul>
        <p style={{ marginTop: '10px', fontSize: '14px', color: '#6B7280' }}>
          Expected API URL: {import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'}
        </p>
      </div>
    </div>
  );
}

export default ConnectionTest;
