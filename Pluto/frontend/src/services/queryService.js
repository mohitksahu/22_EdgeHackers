import api from './apiClient';
import { getSessionId } from './sessionService';

/**
 * Submit a query to the backend
 * @param {string} query - The query text
 * @param {Object} options - Optional settings
 * @returns {Promise} Response containing query results
 */
export const submitQuery = async (query, options = {}) => {
  try {
    const sessionId = getSessionId();
    const response = await api.post('/query/', {
      query,
      session_id: sessionId,
      include_sources: options.include_sources ?? true,
      max_results: options.max_results ?? 10
    });
    return response.data;
  } catch (error) {
    console.error('Query submission failed:', error);
    throw error;
  }
};

/**
 * Check query service health
 * @returns {Promise} Health status
 */
export const checkQueryHealth = async () => {
  try {
    const response = await api.get('/query/health');
    return response.data;
  } catch (error) {
    console.error('Query health check failed:', error);
    throw error;
  }
};

export default {
  submitQuery,
  checkQueryHealth
};
