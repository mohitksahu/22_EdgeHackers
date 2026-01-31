import api from './apiClient';

/**
 * Get vector store statistics
 * @returns {Promise} Vector store stats including document counts by modality
 */
export const getVectorStoreStats = async () => {
  try {
    const response = await api.get('/vector/stats');
    return response.data;
  } catch (error) {
    console.error('Failed to fetch vector store stats:', error);
    throw error;
  }
};

/**
 * Reset vector store (DESTRUCTIVE - use with caution)
 * @returns {Promise} Reset confirmation
 */
export const resetVectorStore = async () => {
  try {
    const response = await api.delete('/vector/reset');
    return response.data;
  } catch (error) {
    console.error('Failed to reset vector store:', error);
    throw error;
  }
};

/**
 * Retrieve similar documents based on a query
 * @param {Object} params - Retrieval parameters
 * @returns {Promise} Retrieved documents
 */
export const retrieveDocuments = async (params) => {
  try {
    const response = await api.post('/retrieval/search', params);
    return response.data;
  } catch (error) {
    console.error('Failed to retrieve documents:', error);
    throw error;
  }
};

export default {
  getVectorStoreStats,
  resetVectorStore,
  retrieveDocuments
};
