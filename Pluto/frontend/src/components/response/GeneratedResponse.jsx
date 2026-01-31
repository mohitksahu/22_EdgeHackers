import AssumptionsList from './AssumptionsList';
import CitationLinks from './CitationLinks';
import RefusalMessage from './RefusalMessage';

function GeneratedResponse({ response }) {
  if (!response) {
    return (
      <div className="card">
        <h2 className="text-2xl font-semibold mb-4">Generated Response</h2>
        <p className="text-gray-600">No response generated yet.</p>
      </div>
    );
  }

  // Check for refusal first
  if (response.refusal) {
    return <RefusalMessage message={response.refusal} />;
  }

  return (
    <div className="card">
      <h2 className="text-2xl font-semibold mb-4">Generated Response</h2>
      <div className="prose max-w-none">
        <p className="text-gray-800 mb-4 whitespace-pre-wrap">{response.content}</p>
        {response.confidence !== undefined && (
          <p className="text-sm text-gray-600 mb-4">
            Confidence Level: {Math.round(response.confidence * 100)}%
          </p>
        )}
        {response.conflicts && response.conflicts.length > 0 && (
          <div className="bg-yellow-50 border border-yellow-200 rounded p-4 mb-4">
            <h3 className="font-medium text-yellow-800 mb-2">⚠️ Detected Conflicts:</h3>
            <ul className="list-disc list-inside text-yellow-700 text-sm space-y-1">
              {response.conflicts.map((conflict, index) => (
                <li key={index}>{conflict}</li>
              ))}
            </ul>
          </div>
        )}
        {response.assumptions && response.assumptions.length > 0 && (
          <AssumptionsList assumptions={response.assumptions} />
        )}
        <CitationLinks citations={response.citations} />
      </div>
    </div>
  );
}

export default GeneratedResponse;
