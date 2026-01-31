function QueryInput({ value, onChange }) {
  return (
    <div>
      <label htmlFor="query" className="block text-sm font-medium text-[var(--text-color,#ffffff)] mb-2">
        Enter your query
      </label>
      <textarea
        id="query"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="Ask a question about the ingested data..."
        className="input-field h-32 resize-none"
        required
      />
    </div>
  );
}

export default QueryInput;
