function SourceCitation({ source }) {
  return (
    <div className="text-sm text-gray-500 border-t pt-2">
      <span className="font-medium">Source: </span>
      {source.filename} {source.page && `(Page ${source.page})`}
      {source.timestamp && ` at ${new Date(source.timestamp).toLocaleString()}`}
    </div>
  );
}

export default SourceCitation;
