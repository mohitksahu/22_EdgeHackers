import api from './apiClient';
import axios from 'axios';

/**
 * Upload a single file for ingestion
 * @param {File} file - The file to upload
 * @param {Object} options - Ingestion options
 * @returns {Promise} Upload result
 */
export const uploadSingleFile = async (file, options = {}) => {
  const formData = new FormData();
  formData.append('file', file);
  
  // Add optional parameters
  if (options.chunking_strategy) {
    formData.append('chunking_strategy', options.chunking_strategy);
  }
  if (options.chunk_size) {
    formData.append('chunk_size', options.chunk_size);
  }
  if (options.chunk_overlap) {
    formData.append('chunk_overlap', options.chunk_overlap);
  }

  try {
    // Create a separate axios instance for file uploads to avoid header conflicts
    const uploadApi = axios.create({
      baseURL: api.defaults.baseURL,
      timeout: api.defaults.timeout,
    });

    const response = await uploadApi.post('/ingest/file', formData);
    return response.data;
  } catch (error) {
    console.error('File upload failed:', error);
    throw error;
  }
};

/**
 * Upload multiple files for batch ingestion
 * @param {File[]} files - Array of files to upload
 * @param {Object} options - Ingestion options
 * @returns {Promise} Upload results
 */
export const uploadBatchFiles = async (files, options = {}) => {
  const formData = new FormData();
  
  files.forEach(file => {
    formData.append('files', file);
  });
  
  // Add optional parameters
  if (options.chunking_strategy) {
    formData.append('chunking_strategy', options.chunking_strategy);
  }
  if (options.chunk_size) {
    formData.append('chunk_size', options.chunk_size);
  }
  if (options.chunk_overlap) {
    formData.append('chunk_overlap', options.chunk_overlap);
  }

  try {
    // Create a separate axios instance for file uploads to avoid header conflicts
    const uploadApi = axios.create({
      baseURL: api.defaults.baseURL,
      timeout: api.defaults.timeout,
    });

    const response = await uploadApi.post('/ingest/batch', formData);
    return response.data;
  } catch (error) {
    console.error('Batch upload failed:', error);
    throw error;
  }
};

/**
 * Get ingestion status
 * @returns {Promise} Ingestion status
 */
export const getIngestionStatus = async () => {
  try {
    const response = await api.get('/ingest/status');
    return response.data;
  } catch (error) {
    console.error('Failed to get ingestion status:', error);
    throw error;
  }
};

export default {
  uploadSingleFile,
  uploadBatchFiles,
  getIngestionStatus
};
