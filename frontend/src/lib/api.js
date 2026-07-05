/**
 * API Configuration and Helper Functions
 */

// API Base URL - will use proxy in development, can be configured for production
const API_BASE_URL = process.env.NODE_ENV === 'production' 
  ? process.env.VITE_API_URL || 'http://localhost:5000'
  : '';

/**
 * Make API request with error handling
 */
export const apiRequest = async (endpoint, options = {}) => {
  const url = `${API_BASE_URL}/api${endpoint}`;
  
  const defaultOptions = {
    headers: {
      'Content-Type': 'application/json',
    },
  };

  const config = {
    ...defaultOptions,
    ...options,
    headers: {
      ...defaultOptions.headers,
      ...options.headers,
    },
  };

  try {
    const response = await fetch(url, config);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      const text = await response.text();
      console.error(`Expected JSON but got: ${contentType}`, text.substring(0, 200));
      throw new Error(`Server returned non-JSON response: ${contentType}`);
    }
    
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`API request failed for ${endpoint}:`, error);
    throw error;
  }
};

/**
 * API endpoints
 */
export const api = {
  // Health check
  health: () => apiRequest('/betting/health'),
  
  // Odds endpoints
  getOdds: (params = {}) => {
    const searchParams = new URLSearchParams(params);
    return apiRequest(`/betting/odds?${searchParams}`);
  },
  
  getGameOdds: (gameId, sport = 'nfl') => 
    apiRequest(`/betting/odds/${gameId}?sport=${sport}`),
  
  // Prediction endpoints
  predictGame: (data) => 
    apiRequest('/betting/predict', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  predictMultipleGames: (data) => 
    apiRequest('/betting/predict/batch', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  analyzeGame: (data) => 
    apiRequest('/betting/analyze', {
      method: 'POST',
      body: JSON.stringify(data),
    }),
  
  // Games endpoints
  getUpcomingGames: (params = {}) => {
    const searchParams = new URLSearchParams(params);
    return apiRequest(`/betting/upcoming?${searchParams}`);
  },
  
  getLiveGames: (params = {}) => {
    const searchParams = new URLSearchParams(params);
    return apiRequest(`/betting/live?${searchParams}`);
  },
  
  getGameDetails: (gameId, sport = 'nfl') => 
    apiRequest(`/betting/games/${gameId}?sport=${sport}`),
  
  getLiveOdds: (gameId, sport = 'nfl') => 
    apiRequest(`/betting/live-odds/${gameId}?sport=${sport}`),
  
  getGameStats: (gameId, sport = 'nfl') => 
    apiRequest(`/betting/stats/${gameId}?sport=${sport}`),
  
  getSports: () => apiRequest('/betting/sports'),

  // ESPN-style endpoints for NCAAF and NFL data
  espn: {
    // Combined scoreboard with NFL and NCAAF
    getScoreboard: (params = {}) => {
      const searchParams = new URLSearchParams(params);
      return apiRequest(`/espn/scoreboard?${searchParams}`);
    },
    
    // Live games only
    getLiveGames: (params = {}) => {
      const searchParams = new URLSearchParams(params);
      return apiRequest(`/espn/live?${searchParams}`);
    },
    
    // Upcoming games
    getUpcomingGames: (params = {}) => {
      const searchParams = new URLSearchParams(params);
      return apiRequest(`/espn/upcoming?${searchParams}`);
    },
    
    // Completed games with scores
    getCompletedGames: (params = {}) => {
      const searchParams = new URLSearchParams(params);
      return apiRequest(`/espn/completed?${searchParams}`);
    },
    
    // NFL games only
    getNFLGames: (params = {}) => {
      const searchParams = new URLSearchParams(params);
      return apiRequest(`/espn/nfl?${searchParams}`);
    },
    
    // NCAAF games only
    getNCAFGames: (params = {}) => {
      const searchParams = new URLSearchParams(params);
      return apiRequest(`/espn/ncaaf?${searchParams}`);
    }
  }
};

export default api;
