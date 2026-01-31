import FileUploader from '../components/ingestion/FileUploader';
import IngestionStatus from '../components/ingestion/IngestionStatus';
import SessionManager from '../components/system/SessionManager';

function Ingest() {
  return (
    <div className="min-h-screen bg-[var(--bg-color,#000000)] text-[var(--text-color,#ffffff)] p-4 py-8">
      <div className="max-w-4xl mx-auto">
        <h1 className="text-3xl font-bold text-[var(--text-color,#ffffff)] mb-6">Data Ingestion</h1>
        <div className="space-y-6">
          <SessionManager />
          <FileUploader />
          <IngestionStatus />
        </div>
      </div>
    </div>
  );
}

export default Ingest;
