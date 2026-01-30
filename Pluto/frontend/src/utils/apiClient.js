// Utility functions for API interactions

export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error status
    return error.response.data.message || 'An error occurred';
  } else if (error.request) {
    // Request was made but no response received
    return 'Network error - please check your connection';
  } else {
    // Something else happened
    return error.message || 'An unexpected error occurred';
  }
};

export const formatApiResponse = (response) => {
  // Format response data as needed
  return response.data;
};
