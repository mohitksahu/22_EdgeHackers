function EvidenceCard({ evidence }) {
  const renderContent = () => {
    switch (evidence.modality) {
      case 'text':
        return <p className="text-gray-800">{evidence.content}</p>;
      case 'image':
        return (
          <div>
            <img src={evidence.content} alt="Evidence" className="max-w-full h-auto rounded" />
            {evidence.extractedText && (
              <p className="text-gray-600 mt-2">{evidence.extractedText}</p>
            )}
          </div>
        );
      case 'audio':
        return (
          <div>
            <audio controls className="w-full">
              <source src={evidence.content} type="audio/mpeg" />
            </audio>
            {evidence.transcript && (
              <p className="text-gray-600 mt-2">{evidence.transcript}</p>
            )}
          </div>
        );
      default:
        return <p className="text-gray-800">{evidence.content}</p>;
    }
  };

  return (
    <div className="mb-4">
      {renderContent()}
    </div>
  );
}

export default EvidenceCard;
