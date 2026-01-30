import { useState, useEffect } from 'react';
import { getIngestionStatus } from '../../services/ingestionService';

function IngestionStatus() {
  const [status, setStatus] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const response = await getIngestionStatus();
        setStatus(response);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch status:', err);
        setError('Failed to fetch ingestion status');
      } finally {
        setLoading(false);
      }
    };

    fetchStatus();
    const interval = setInterval(fetchStatus, 5000); // Poll every 5 seconds

    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="card">
        <h2 className="text-2xl font-semibold mb-4">Ingestion Status</h2>
        <p className="text-[var(--secondary-text,#6b7280)]">Loading...</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="text-2xl font-semibold mb-4">Ingestion Status</h2>
      {error ? (
        <p className="text-red-500">{error}</p>
      ) : !status || (Array.isArray(status) && status.length === 0) ? (
        <p className="text-[var(--secondary-text,#6b7280)]">No recent ingestions.</p>
      ) : Array.isArray(status) ? (
        <ul className="space-y-2">
          {status.map((item, index) => (
            <li key={index} className="flex justify-between items-center">
              <span>{item.filename || 'Unknown file'}</span>
              <span className={`px-2 py-1 rounded text-sm ${
                item.status === 'completed' || item.status === 'success' ? 'bg-green-100 text-green-800' :
                item.status === 'processing' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {item.status}
              </span>
            </li>
          ))}
        </ul>
      ) : (
        <div className="space-y-2">
          <p className="text-sm text-[var(--secondary-text,#6b7280)]">
            {status.message || 'System ready for ingestion'}
          </p>
        </div>
      )}
    </div>
  );
}

export default IngestionStatus;
