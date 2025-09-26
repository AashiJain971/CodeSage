// /Users/adityajain/CodeSageIITD/frontend/src/lib/api.js
// API helper functions for CodeSage backend integration

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
const WS_BASE_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

// Helper to construct API URLs
export function apiUrl(path = '') {
  // Ensure path starts with /
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${BASE_URL}${cleanPath}`;
}

// Generic fetch wrapper with error handling
export async function apiFetch(path, options = {}) {
  const url = apiUrl(path);
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  };
  
  const mergedOptions = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, mergedOptions);
    
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }
    
    // Handle different content types
    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    return await response.text();
  } catch (error) {
    console.error(`API call failed for ${url}:`, error);
    throw error;
  }
}

// WebSocket URL helper
export function wsUrl(path = '/ws') {
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  return `${WS_BASE_URL}${cleanPath}`;
}

// Specific API functions based on backend structure

// Interview endpoints
export const interviewAPI = {
  // Get available interview categories/types
  getCategories: () => apiFetch('/api/interviews/options'),
  
  // Start interview session
  startInterview: (data) => apiFetch('/interview/start', {
    method: 'POST',
    body: JSON.stringify(data),
  }),
  
  // Get interview summary
  getSummary: (interviewId) => apiFetch(`/interview/summary/${interviewId}`),
  
  // Upload resume
  uploadResume: (formData) => fetch(apiUrl('/resume/upload'), {
    method: 'POST',
    body: formData, // Don't set Content-Type for FormData
  }),
  
  // Get technical categories
  getTechnicalCategories: () => apiFetch('/interview/categories'),
};

// WebSocket connection helper
export function createWebSocket(path = '/ws', options = {}) {
  const url = wsUrl(path);
  const ws = new WebSocket(url);
  
  // Add common event handlers if provided
  if (options.onOpen) ws.onopen = options.onOpen;
  if (options.onMessage) ws.onmessage = options.onMessage;
  if (options.onError) ws.onerror = options.onError;
  if (options.onClose) ws.onclose = options.onClose;
  
  return ws;
}

// File upload helper
export async function uploadFile(endpoint, file, additionalData = {}) {
  const formData = new FormData();
  formData.append('file', file);
  
  // Add any additional form fields
  Object.keys(additionalData).forEach(key => {
    formData.append(key, additionalData[key]);
  });
  
  return fetch(apiUrl(endpoint), {
    method: 'POST',
    body: formData,
  });
}

// Audio endpoints (based on backend structure)
export const audioAPI = {
  // Upload audio for transcription
  uploadAudio: (audioBlob, filename = 'audio.wav') => {
    const formData = new FormData();
    formData.append('audio', audioBlob, filename);
    return fetch(apiUrl('/audio/upload'), {
      method: 'POST',
      body: formData,
    });
  },
  
  // Get audio file
  getAudio: (filename) => apiUrl(`/audio/${filename}`),
};

export default {
  apiUrl,
  apiFetch,
  wsUrl,
  createWebSocket,
  uploadFile,
  interviewAPI,
  audioAPI,
};