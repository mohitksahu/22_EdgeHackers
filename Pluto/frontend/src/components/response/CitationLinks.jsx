function CitationLinks({ citations }) {
  if (!citations || citations.length === 0) {
    return null;
  }

  return (
    <div className="mb-4">
      <h3 className="font-medium text-gray-800 mb-2">Sources Cited:</h3>
      <ul className="list-disc list-inside text-gray-600 space-y-1">
        {citations.map((citation, index) => (
          <li key={index}>
            {citation.filename} {citation.page && `(Page ${citation.page})`}
          </li>
        ))}
      </ul>
    </div>
  );
}

export default CitationLinks;
