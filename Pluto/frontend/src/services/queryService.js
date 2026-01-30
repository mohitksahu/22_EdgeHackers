import api from './apiClient';

/**
 * Submit a query to the backend
 * @param {string} query - The query text
 * @param {string} userId - Optional user identifier
 * @returns {Promise} Response containing query results
 */
export const submitQuery = async (query, userId = 'default_user') => {
  try {
    const response = await api.post('/query/', {
      query,
      user_id: userId
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
