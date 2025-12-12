// api.js - API utility functions for EasyApt

// Get the API base URL - adjust this based on your server setup
const API_BASE_URL = window.location.origin;

/**
 * Get the JWT token from localStorage
 */
export function getToken() {
  return localStorage.getItem('easyapt_token');
}

/**
 * Set the JWT token in localStorage
 */
export function setToken(token) {
  localStorage.setItem('easyapt_token', token);
}

/**
 * Remove the JWT token from localStorage
 */
export function removeToken() {
  localStorage.removeItem('easyapt_token');
}

/**
 * Check if user is logged in
 */
export function isLoggedIn() {
  return !!getToken();
}

/**
 * Make an API request with proper headers
 */
async function apiRequest(endpoint, options = {}) {
  const token = getToken();

  const config = {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
  };

  // Add authorization header if token exists
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    // Handle different response types
    const contentType = response.headers.get('content-type');
    let data;

    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      // Check if session expired
      if (response.status === 401 && data.detail && data.detail.includes('Session expired')) {
        alert('Your session has expired due to inactivity. Please log in again.');
        removeToken();
        window.location.href = '/login.html';
        return;
      }
      
      throw new Error(data.detail || data || `HTTP error! status: ${response.status}`);
    }

    return data;
  } catch (error) {
    console.error('API request failed:', error);
    throw error;
  }
}
/**
 * Auth API calls
 */
export const auth = {
  async register(email, password) {
    return apiRequest('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  },

async login(email, password, recaptchaToken) {
    const params = new URLSearchParams({
      username: email,
      password: password,
    });
    
    if (recaptchaToken) {
      params.append('recaptcha_token', recaptchaToken);
    }
    
    const response = await fetch(`${API_BASE_URL}/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    setToken(data.access_token);
    return data;
  },

  async getCurrentUser() {
    return apiRequest('/auth/me');
  },

  logout() {
    removeToken();
    window.location.href = '/login.html';
  },
};

/**
 * Profile API calls
 */
export const profile = {
  async get() {
    return apiRequest('/profile/me');
  },

  async update(profileData) {
    return apiRequest('/profile/me', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  },
};

/**
 * Appointments API calls
 */
export const appointments = {
  async getMyAppointments() {
    return apiRequest('/appointments/my');
  },

  async book(providerId, startTime, endTime, reason) {
    return apiRequest('/appointments/book', {
      method: 'POST',
      body: JSON.stringify({
        provider_id: providerId,
        start_time: startTime,
        end_time: endTime,
        reason: reason,
      }),
    });
  },

  async reschedule(appointmentId, startTime, endTime) {
    return apiRequest(`/appointments/${appointmentId}/reschedule`, {
      method: 'PUT',
      body: JSON.stringify({
        start_time: startTime,
        end_time: endTime,
      }),
    });
  },

  async cancel(appointmentId) {
    return apiRequest(`/appointments/${appointmentId}`, {
      method: 'DELETE',
    });
  },
};

/**
 * Providers API calls
 */
export const providers = {
  async search(query) {
    return apiRequest(`/providers/search?q=${encodeURIComponent(query)}`);
  },

  async getAppointments(providerId) {
    return apiRequest(`/providers/${providerId}/appointments`);
  },

  async getDashboard() {
    return apiRequest('/provider-dashboard-list');
  },
};

/**
 * Utility function to show error messages
 */
export function showError(elementId, message) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = message;
    element.className = 'alert alert-error';
    element.classList.remove('hidden');
  }
}

/**
 * Utility function to show success messages
 */
export function showSuccess(elementId, message) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = message;
    element.className = 'alert alert-success';
    element.classList.remove('hidden');
  }
}

/**
 * Utility function to show info messages
 */
export function showInfo(elementId, message) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = message;
    element.className = 'alert alert-info';
    element.classList.remove('hidden');
  }
}

/**
 * Utility function to clear messages
 */
export function clearMessage(elementId) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = '';
    element.className = 'hidden';
  }
}

/**
 * Format date/time for display
 */
export function formatDateTime(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return isoString;
  
  return date.toLocaleString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Format date only
 */
export function formatDate(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return isoString;
  
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

/**
 * Format time only
 */
export function formatTime(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return isoString;
  
  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Redirect to login if not authenticated
 */
export function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = '/login.html';
    return false;
  }
  return true;
}
