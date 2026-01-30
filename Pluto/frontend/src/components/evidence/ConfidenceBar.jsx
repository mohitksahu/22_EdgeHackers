function ConfidenceBar({ confidence }) {
  const percentage = Math.round(confidence * 100);

  return (
    <div className="flex items-center space-x-2">
      <span className="text-sm text-gray-600">Confidence:</span>
      <div className="w-24 bg-gray-200 rounded-full h-2">
        <div
          className="bg-blue-600 h-2 rounded-full"
          style={{ width: `${percentage}%` }}
        ></div>
      </div>
      <span className="text-sm text-gray-600">{percentage}%</span>
    </div>
  );
}

export default ConfidenceBar;
