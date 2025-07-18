/**
 * API utility functions for communicating with the Fledermaus Tracking backend.
 */

const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

/**
 * Check if the API server is healthy.
 */
export const checkApiHealth = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return await response.json();
  } catch (error) {
    console.error('API health check failed:', error);
    throw new Error('Backend server is not available');
  }
};

/**
 * Analyze a video file for bat detection.
 * 
 * @param {File} videoFile - The video file to analyze
 * @param {number} startTime - Start time in seconds
 * @param {number} endTime - End time in seconds (optional)
 * @param {number} uploadSensitivity - Detection sensitivity
 * @returns {Promise<object>} Analysis results
 */
export const analyzeVideo = async (videoFile, startTime = 0, endTime = null, uploadSensitivity = 1.0) => {
  try {
    // Validate inputs
    if (!videoFile) {
      throw new Error('Video file is required');
    }
    
    if (startTime < 0) {
      throw new Error('Start time must be non-negative');
    }
    
    if (endTime !== null && endTime <= startTime) {
      throw new Error('End time must be greater than start time');
    }
    
    // Create form data
    const formData = new FormData();
    formData.append('file', videoFile);
    formData.append('start_time', startTime.toString());
    if (endTime !== null) {
      formData.append('end_time', endTime.toString());
    }
    formData.append('upload_sensitivity', uploadSensitivity.toString());
    
    // Make API request
    const response = await fetch(`${API_BASE_URL}/analyze`, {
      method: 'POST',
      body: formData,
    });
    
    const result = await response.json();
    
    if (!response.ok) {
      throw new Error(result.message || 'Analysis failed');
    }
    
    if (!result.success) {
      throw new Error(result.message || 'Analysis was not successful');
    }
    
    return result.data;
    
  } catch (error) {
    console.error('Video analysis failed:', error);
    throw error;
  }
};

/**
 * Get basic API information.
 */
export const getApiInfo = async () => {
  try {
    const response = await fetch(`${API_BASE_URL}/`);
    return await response.json();
  } catch (error) {
    console.error('Failed to get API info:', error);
    throw error;
  }
};