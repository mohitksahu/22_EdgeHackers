import { useState } from 'react';
import { uploadSingleFile, uploadBatchFiles } from '../../services/ingestionService';

function FileUploader() {
  const [files, setFiles] = useState([]);
  const [uploading, setUploading] = useState(false);
  const [uploadResults, setUploadResults] = useState([]);
  const [error, setError] = useState(null);
  const [chunkingStrategy, setChunkingStrategy] = useState('character');
  const [chunkSize, setChunkSize] = useState(1000);
  const [chunkOverlap, setChunkOverlap] = useState(200);

  const ALLOWED_EXTENSIONS = ['.pdf', '.doc', '.docx', '.txt', '.png', '.jpg', '.jpeg', '.mp3', '.wav'];

  const validateFiles = (fileList) => {
    const invalidFiles = [];
    fileList.forEach(file => {
      const extension = '.' + file.name.split('.').pop().toLowerCase();
      if (!ALLOWED_EXTENSIONS.includes(extension)) {
        invalidFiles.push(file.name);
      }
    });
    return invalidFiles;
  };

  const handleFileChange = (e) => {
    const selectedFiles = Array.from(e.target.files);
    const invalidFiles = validateFiles(selectedFiles);
    
    if (invalidFiles.length > 0) {
      setError(`Unsupported file type(s): ${invalidFiles.join(', ')}. Only PDF, DOC, DOCX, TXT, PNG, JPG, JPEG, MP3, and WAV files are allowed.`);
      setFiles([]);
      e.target.value = ''; // Clear input
      return;
    }
    
    setFiles(selectedFiles);
    setError(null);
    setUploadResults([]);
  };

  const handleUpload = async () => {
    if (files.length === 0) return;

    setUploading(true);
    setError(null);
    setUploadResults([]);

    const options = {
      chunking_strategy: chunkingStrategy,
      chunk_size: parseInt(chunkSize),
      chunk_overlap: parseInt(chunkOverlap)
    };

    try {
      if (files.length === 1) {
        // Upload single file
        const result = await uploadSingleFile(files[0], options);
        setUploadResults([result]);
      } else {
        // Upload multiple files as batch
        const results = await uploadBatchFiles(files, options);
        setUploadResults(Array.isArray(results) ? results : [results]);
      }
      
      setFiles([]);
    } catch (err) {
      setError(err.response?.data?.detail || err.message || 'Upload failed');
      console.error('Upload error:', err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="text-2xl font-semibold mb-4">Upload Files</h2>
      <div className="space-y-4">
        <input
          type="file"
          multiple
          accept=".pdf,.doc,.docx,.txt,.png,.jpg,.jpeg,.mp3,.wav"
          onChange={handleFileChange}
          className="input-field"
          disabled={uploading}
        />
        <p className="text-xs text-[var(--secondary-text,#9ca3af)] mt-2">
          Allowed formats: PDF, DOC, DOCX, TXT, PNG, JPG, JPEG, MP3, WAV
        </p>
        
        {/* Chunking Options */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div>
            <label className="block text-sm font-medium mb-1">Chunking Strategy</label>
            <select
              value={chunkingStrategy}
              onChange={(e) => setChunkingStrategy(e.target.value)}
              className="input-field"
              disabled={uploading}
            >
              <option value="character">Character</option>
              <option value="sentence">Sentence</option>
              <option value="page">Page</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Chunk Size</label>
            <input
              type="number"
              value={chunkSize}
              onChange={(e) => setChunkSize(e.target.value)}
              className="input-field"
              min="100"
              max="5000"
              disabled={uploading}
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">Chunk Overlap</label>
            <input
              type="number"
              value={chunkOverlap}
              onChange={(e) => setChunkOverlap(e.target.value)}
              className="input-field"
              min="0"
              max="500"
              disabled={uploading}
            />
          </div>
        </div>

        {files.length > 0 && (
          <div>
            <h3 className="font-medium mb-2">Selected Files ({files.length}):</h3>
            <ul className="list-disc list-inside text-sm">
              {files.map((file, index) => (
                <li key={index}>{file.name} ({(file.size / 1024).toFixed(2)} KB)</li>
              ))}
            </ul>
          </div>
        )}

        {error && (
          <div className="bg-red-500/10 border border-red-500 text-red-500 px-4 py-3 rounded">
            {error}
          </div>
        )}

        {uploadResults.length > 0 && (
          <div className="bg-green-500/10 border border-green-500 text-green-500 px-4 py-3 rounded">
            <h3 className="font-medium mb-2">Upload Successful!</h3>
            {uploadResults.map((result, index) => (
              <div key={index} className="text-sm">
                {result.stored_chunks && (
                  <p>Stored {result.stored_chunks} chunks from {result.filename || `file ${index + 1}`}</p>
                )}
              </div>
            ))}
          </div>
        )}

        <button
          onClick={handleUpload}
          disabled={uploading || files.length === 0}
          className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {uploading ? 'Uploading...' : 'Upload Files'}
        </button>
      </div>
    </div>
  );
}

export default FileUploader;
