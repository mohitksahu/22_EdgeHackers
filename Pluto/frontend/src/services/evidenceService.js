import api from './apiClient';

/**
 * Get evidence for a specific query or document
 * @param {string} queryId - The query ID
 * @returns {Promise} Evidence data
 */
export const getEvidence = async (queryId) => {
  try {
    const response = await api.get(`/evidence/${queryId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch evidence:', error);
    throw error;
  }
};

/**
 * Get evidence by source
 * @param {string} sourceId - The source document ID
 * @returns {Promise} Evidence from specific source
 */
export const getEvidenceBySource = async (sourceId) => {
  try {
    const response = await api.get(`/evidence/source/${sourceId}`);
    return response.data;
  } catch (error) {
    console.error('Failed to fetch evidence by source:', error);
    throw error;
  }
};

export default {
  getEvidence,
  getEvidenceBySource
};
