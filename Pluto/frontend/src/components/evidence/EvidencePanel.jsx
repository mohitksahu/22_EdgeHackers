import EvidenceCard from './EvidenceCard';
import ConfidenceBar from './ConfidenceBar';
import SourceCitation from './SourceCitation';

function EvidencePanel({ evidence }) {
  if (!evidence || evidence.length === 0) {
    return (
      <div className="card">
        <h2 className="text-2xl font-semibold mb-4">Evidence</h2>
        <p className="text-gray-600">No evidence found for this query.</p>
      </div>
    );
  }

  return (
    <div className="card">
      <h2 className="text-2xl font-semibold mb-4">Retrieved Evidence</h2>
      <div className="space-y-4">
        {evidence.map((item, index) => (
          <div key={index} className="border rounded-lg p-4">
            <div className="flex justify-between items-start mb-2">
              <span className="font-medium text-sm text-gray-600 uppercase">
                {item.modality}
              </span>
              <ConfidenceBar confidence={item.confidence} />
            </div>
            <EvidenceCard evidence={item} />
            <SourceCitation source={item.source} />
          </div>
        ))}
      </div>
    </div>
  );
}

export default EvidencePanel;
