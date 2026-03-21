// api.js - API utility functions for EasyApt

const API_BASE_URL = window.location.origin;

/**
 * JWT token helpers
 */
export function getToken() {
  return localStorage.getItem('easyapt_token');
}

export function setToken(token) {
  localStorage.setItem('easyapt_token', token);
}

export function removeToken() {
  localStorage.removeItem('easyapt_token');
}

/**
 * Temporary login token for 2FA step
 */
export function getTemp2FAToken() {
  return sessionStorage.getItem('easyapt_temp_2fa_token');
}

export function setTemp2FAToken(token) {
  sessionStorage.setItem('easyapt_temp_2fa_token', token);
}

export function removeTemp2FAToken() {
  sessionStorage.removeItem('easyapt_temp_2fa_token');
}

export function isLoggedIn() {
  return !!getToken();
}

/**
 * Generic API request helper
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

  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`;
  }

  try {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, config);

    const contentType = response.headers.get('content-type');
    let data;

    if (contentType && contentType.includes('application/json')) {
      data = await response.json();
    } else {
      data = await response.text();
    }

    if (!response.ok) {
      if (response.status === 401 && data.detail && data.detail.includes('Session expired')) {
        alert('Your session has expired due to inactivity. Please log in again.');
        removeToken();
        removeTemp2FAToken();
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

  async loginStart(email, password, recaptchaToken) {
    const params = new URLSearchParams({
      username: email,
      password: password,
      recaptcha_token: recaptchaToken,
    });

    const response = await fetch(`${API_BASE_URL}/auth/login/start`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params,
    });

    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Login failed');
    }

    if (data.requires_2fa && data.temp_token) {
      setTemp2FAToken(data.temp_token);
      return data;
    }

    if (data.access_token) {
      setToken(data.access_token);
      removeTemp2FAToken();
    }

    return data;
  },

  async verify2FA(code) {
    const tempToken = getTemp2FAToken();

    if (!tempToken) {
      throw new Error('2FA session expired. Please log in again.');
    }

    const data = await apiRequest('/auth/login/verify-2fa', {
      method: 'POST',
      body: JSON.stringify({
        temp_token: tempToken,
        code,
      }),
    });

    if (data.access_token) {
      setToken(data.access_token);
      removeTemp2FAToken();
    }

    return data;
  },

  async getCurrentUser() {
    return apiRequest('/auth/me');
  },

  async get2FAStatus() {
    return apiRequest('/auth/2fa/status');
  },

  async start2FASetup() {
    return apiRequest('/auth/2fa/setup/start', {
      method: 'POST',
    });
  },

  async verify2FASetup(code) {
    return apiRequest('/auth/2fa/setup/verify', {
      method: 'POST',
      body: JSON.stringify({ code }),
    });
  },

  async disable2FA(password, code) {
    return apiRequest('/auth/2fa/disable', {
      method: 'POST',
      body: JSON.stringify({ password, code }),
    });
  },

  async regenerateBackupCodes() {
    return apiRequest('/auth/2fa/backup-codes/regenerate', {
      method: 'POST',
    });
  },

  async ping() {
    return apiRequest('/auth/ping', {
      method: 'POST',
    });
  },

  logout() {
    removeToken();
    removeTemp2FAToken();
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
 * UI helpers
 */
export function showError(elementId, message) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = message;
    element.className = 'alert alert-error';
    element.classList.remove('hidden');
  }
}

export function showSuccess(elementId, message) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = message;
    element.className = 'alert alert-success';
    element.classList.remove('hidden');
  }
}

export function showInfo(elementId, message) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = message;
    element.className = 'alert alert-info';
    element.classList.remove('hidden');
  }
}

export function clearMessage(elementId) {
  const element = document.getElementById(elementId);
  if (element) {
    element.textContent = '';
    element.className = 'hidden';
  }
}

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

export function formatTime(isoString) {
  if (!isoString) return '';
  const date = new Date(isoString);
  if (isNaN(date.getTime())) return isoString;

  return date.toLocaleTimeString('en-US', {
    hour: '2-digit',
    minute: '2-digit',
  });
}

export function requireAuth() {
  if (!isLoggedIn()) {
    window.location.href = '/login.html';
    return false;
  }
  return true;
}

/**
 * Session Timeout Message
 */

let sessionMonitorInitialized = false;

export function initSessionMonitor({
  timeoutSeconds = 60,
  warningSeconds = 20,
  minPingIntervalMs = 120000,
} = {}) {
  if (sessionMonitorInitialized) return;
  sessionMonitorInitialized = true;

  let warningTimer = null;
  let expireTimer = null;
  let countdownInterval = null;
  let remainingSeconds = warningSeconds;
  let lastPingAt = Date.now();
  let modalVisible = false;

  const overlay = document.createElement('div');
  overlay.id = 'session-warning-overlay';
  overlay.style.cssText = `
    display: none;
    position: fixed;
    inset: 0;
    background: rgba(0,0,0,0.35);
    z-index: 9999;
    align-items: center;
    justify-content: center;
  `;

  const modal = document.createElement('div');
  modal.style.cssText = `
    background: white;
    width: min(90vw, 460px);
    border-radius: 16px;
    padding: 24px;
    box-shadow: 0 20px 50px rgba(0,0,0,0.25);
    text-align: center;
    font-family: inherit;
  `;

  modal.innerHTML = `
    <h2 id="session-warning-title" style="margin:0 0 12px 0;">Are you still there?</h2>
    <p id="session-warning-text" style="margin:0 0 18px 0; color:#555;">
      Your session will expire soon.
    </p>
    <button id="session-stay-btn" type="button" class="btn btn-primary" style="min-width:180px;">
      Stay Logged In
    </button>
  `;

  overlay.appendChild(modal);
  document.body.appendChild(overlay);

  const titleEl = modal.querySelector('#session-warning-title');
  const textEl = modal.querySelector('#session-warning-text');
  const stayBtn = modal.querySelector('#session-stay-btn');

  function showOverlay() {
    overlay.style.display = 'flex';
    modalVisible = true;
  }

  function hideOverlay() {
    overlay.style.display = 'none';
    modalVisible = false;
    clearInterval(countdownInterval);
    countdownInterval = null;
  }

  function showWelcomeMessage() {
    titleEl.textContent = 'There you are! :)';
    textEl.textContent = 'Your session is still active.';
    showOverlay();

    setTimeout(() => {
      hideOverlay();
      titleEl.textContent = 'Are you still there?';
    }, 1200);
  }

  function scheduleTimers() {
    clearTimeout(warningTimer);
    clearTimeout(expireTimer);
    clearInterval(countdownInterval);

    warningTimer = setTimeout(() => {
      remainingSeconds = warningSeconds;
      titleEl.textContent = 'Are you still there?';
      textEl.textContent = `Your session will expire in ${remainingSeconds} seconds unless we detect activity.`;
      showOverlay();

      countdownInterval = setInterval(() => {
        remainingSeconds -= 1;
        if (remainingSeconds <= 0) {
          clearInterval(countdownInterval);
          countdownInterval = null;
          auth.logout();
          return;
        }
        textEl.textContent = `Your session will expire in ${remainingSeconds} seconds unless we detect activity.`;
      }, 1000);
    }, (timeoutSeconds - warningSeconds) * 1000);

    expireTimer = setTimeout(() => {
      auth.logout();
    }, timeoutSeconds * 1000);
  }

  async function refreshSession(showGreeting = false) {
    try {
      const now = Date.now();

      if (now - lastPingAt >= minPingIntervalMs || modalVisible) {
        await auth.ping();
        lastPingAt = now;
      }

      scheduleTimers();

      if (showGreeting) {
        showWelcomeMessage();
      } else if (modalVisible) {
        hideOverlay();
      }
    } catch (error) {
      console.error('Session refresh failed:', error);
      auth.logout();
    }
  }

  function activityHandler() {
    if (modalVisible) {
      refreshSession(true);
      return;
    }

    scheduleTimers();

    const now = Date.now();
    if (now - lastPingAt >= minPingIntervalMs) {
      refreshSession(false);
    }
  }

  stayBtn.addEventListener('click', () => refreshSession(true));
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) {
      refreshSession(true);
    }
  });

  ['click', 'mousemove', 'keydown', 'scroll', 'touchstart'].forEach((eventName) => {
    document.addEventListener(eventName, activityHandler, { passive: true });
  });

  scheduleTimers();
}