function AssumptionsList({ assumptions }) {
  if (!assumptions || assumptions.length === 0) {
    return null;
  }

  return (
    <div className="mb-4">
      <h3 className="font-medium text-gray-800 mb-2">Assumptions Made:</h3>
      <ul className="list-disc list-inside text-gray-600 space-y-1">
        {assumptions.map((assumption, index) => (
          <li key={index}>{assumption}</li>
        ))}
      </ul>
    </div>
  );
}

export default AssumptionsList;
