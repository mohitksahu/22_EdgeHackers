function RefusalMessage({ message }) {
  return (
    <div className="card border-red-200 bg-red-50">
      <h2 className="text-2xl font-semibold mb-4 text-red-800">Response Refused</h2>
      <div className="bg-white border border-red-200 rounded p-4">
        <p className="text-red-700">{message}</p>
      </div>
    </div>
  );
}

export default RefusalMessage;
