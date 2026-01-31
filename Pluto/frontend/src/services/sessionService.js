/**
 * Session Service - Manages session IDs and syncs with backend
 * Integrates with the existing "planet" (notebook) system
 */
import api from './apiClient';

const SESSION_KEY = 'pluto_session_id';
const PLANET_HISTORY_KEY = 'planetHistory';

/**
 * Get current session ID (synced with active planet)
 */
export const getSessionId = () => {
  const activePlanet = getActivePlanet();
  if (activePlanet?.sessionId) {
    return activePlanet.sessionId;
  }

  let sessionId = localStorage.getItem(SESSION_KEY);
  if (!sessionId) {
    sessionId = createNewSession();
  }
  
  return sessionId;
};

/**
 * Get currently active planet
 */
export const getActivePlanet = () => {
  const activePlanetId = localStorage.getItem('activePlanetId');
  if (!activePlanetId) return null;

  const planetHistory = JSON.parse(localStorage.getItem(PLANET_HISTORY_KEY) || '[]');
  return planetHistory.find(p => p.id === activePlanetId);
};

/**
 * Set active planet
 */
export const setActivePlanet = (planetId) => {
  localStorage.setItem('activePlanetId', planetId);
  
  const planetHistory = JSON.parse(localStorage.getItem(PLANET_HISTORY_KEY) || '[]');
  const planet = planetHistory.find(p => p.id === planetId);
  
  if (planet?.sessionId) {
    localStorage.setItem(SESSION_KEY, planet.sessionId);
  }
};

/**
 * Create new session ID
 */
export const createNewSession = () => {
  const timestamp = Date.now();
  const random = Math.random().toString(36).substring(2, 15);
  const sessionId = `session-${timestamp}-${random}`;
  
  localStorage.setItem(SESSION_KEY, sessionId);
  return sessionId;
};

/**
 * Create new planet with its own session
 */
export const createNewPlanet = (name = 'Untitled Planet') => {
  const sessionId = createNewSession();
  const planetId = `planet-${Date.now()}`;
  
  const planet = {
    id: planetId,
    sessionId: sessionId,
    name: name,
    messages: [],
    timestamp: new Date().toISOString(),
    sources: 0,
  };

  const planetHistory = JSON.parse(localStorage.getItem(PLANET_HISTORY_KEY) || '[]');
  planetHistory.unshift(planet);
  localStorage.setItem(PLANET_HISTORY_KEY, JSON.stringify(planetHistory.slice(0, 20)));
  
  setActivePlanet(planetId);
  return planet;
};

/**
 * Update planet data
 */
export const updatePlanet = (planetId, updates) => {
  const planetHistory = JSON.parse(localStorage.getItem(PLANET_HISTORY_KEY) || '[]');
  const index = planetHistory.findIndex(p => p.id === planetId);
  
  if (index >= 0) {
    planetHistory[index] = {
      ...planetHistory[index],
      ...updates,
      timestamp: new Date().toISOString(),
    };
    localStorage.setItem(PLANET_HISTORY_KEY, JSON.stringify(planetHistory));
  }
};

/**
 * Get session info from backend
 */
export const getSessionInfo = async () => {
  try {
    const response = await api.get('/session/info');
    return response.data;
  } catch (error) {
    console.error('Failed to get session info:', error);
    throw error;
  }
};

/**
 * Clear current session
 */
export const clearSession = async (clearDocuments = true, clearChatHistory = true) => {
  try {
    const response = await api.delete('/session/clear', {
      params: { clear_documents: clearDocuments, clear_chat_history: clearChatHistory }
    });
    
    const activePlanetId = localStorage.getItem('activePlanetId');
    if (activePlanetId) {
      updatePlanet(activePlanetId, { messages: [], sources: 0 });
    }
    
    return response.data;
  } catch (error) {
    console.error('Failed to clear session:', error);
    throw error;
  }
};

/**
 * Delete planet and its backend data
 */
export const deletePlanet = async (planetId) => {
  const planetHistory = JSON.parse(localStorage.getItem(PLANET_HISTORY_KEY) || '[]');
  const planet = planetHistory.find(p => p.id === planetId);
  
  if (planet?.sessionId) {
    const currentSessionId = getSessionId();
    localStorage.setItem(SESSION_KEY, planet.sessionId);
    
    try {
      await clearSession(true, true);
    } catch (error) {
      console.error('Failed to clear backend data:', error);
    } finally {
      localStorage.setItem(SESSION_KEY, currentSessionId);
    }
  }
  
  const updatedHistory = planetHistory.filter(p => p.id !== planetId);
  localStorage.setItem(PLANET_HISTORY_KEY, JSON.stringify(updatedHistory));
  
  if (localStorage.getItem('activePlanetId') === planetId) {
    localStorage.removeItem('activePlanetId');
    createNewSession();
  }
};

export const renamePlanet = (planetId, newName) => updatePlanet(planetId, { name: newName });
export const getAllPlanets = () => JSON.parse(localStorage.getItem(PLANET_HISTORY_KEY) || '[]');
export const switchToPlanet = (planetId) => {
  setActivePlanet(planetId);
  return getAllPlanets().find(p => p.id === planetId);
};