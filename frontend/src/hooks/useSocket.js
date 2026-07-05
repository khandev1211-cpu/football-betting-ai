/**
 * React Hook for Socket.IO Integration
 * Provides real-time data management for betting components
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import socketService from '../services/socketService';

export const useSocket = (serverUrl = 'http://localhost:5000') => {
  const [isConnected, setIsConnected] = useState(false);
  const [connectionError, setConnectionError] = useState(null);
  const [liveGames, setLiveGames] = useState([]);
  const [liveOpportunities, setLiveOpportunities] = useState([]);
  const [gameAnalysis, setGameAnalysis] = useState({});
  const [analysisLoading, setAnalysisLoading] = useState({});
  const subscribedGames = useRef(new Set());

  // Connect to socket on mount
  useEffect(() => {
    socketService.connect(serverUrl);

    // Subscribe to connection events
    const unsubscribeConnection = socketService.subscribe('connection', (data) => {
      setIsConnected(data.status === 'connected');
      if (data.status === 'error') {
        setConnectionError(data.error);
      } else {
        setConnectionError(null);
      }
    });

    // Subscribe to game updates
    const unsubscribeGameUpdate = socketService.subscribe('game_update', (data) => {
      setLiveGames(prevGames => {
        const updatedGames = [...prevGames];
        const gameIndex = updatedGames.findIndex(game => game.game_id === data.game_id);
        
        if (gameIndex >= 0) {
          updatedGames[gameIndex] = { ...updatedGames[gameIndex], ...data.data };
        } else {
          updatedGames.push(data.data);
        }
        
        return updatedGames;
      });
    });

    // Subscribe to odds updates
    const unsubscribeOddsUpdate = socketService.subscribe('odds_update', (data) => {
      setLiveGames(prevGames => {
        const updatedGames = [...prevGames];
        const gameIndex = updatedGames.findIndex(game => game.game_id === data.game_id);
        
        if (gameIndex >= 0) {
          updatedGames[gameIndex] = {
            ...updatedGames[gameIndex],
            odds_data: { ...updatedGames[gameIndex].odds_data, ...data.odds_data },
            last_odds_update: data.timestamp
          };
        }
        
        return updatedGames;
      });
    });

    // Subscribe to live opportunities
    const unsubscribeLiveOpportunities = socketService.subscribe('live_opportunities', (data) => {
      setLiveOpportunities(data.opportunities || []);
    });

    // Subscribe to analysis events
    const unsubscribeAnalysisStarted = socketService.subscribe('analysis_started', (data) => {
      setAnalysisLoading(prev => ({ ...prev, [data.game_id]: true }));
    });

    const unsubscribeAnalysisComplete = socketService.subscribe('analysis_complete', (data) => {
      setGameAnalysis(prev => ({ ...prev, [data.game_id]: data.analysis }));
      setAnalysisLoading(prev => ({ ...prev, [data.game_id]: false }));
    });

    const unsubscribeAnalysisError = socketService.subscribe('analysis_error', (data) => {
      setAnalysisLoading(prev => ({ ...prev, [data.game_id]: false }));
      console.error('Analysis error for game', data.game_id, ':', data.error);
    });

    // Cleanup on unmount
    return () => {
      unsubscribeConnection();
      unsubscribeGameUpdate();
      unsubscribeOddsUpdate();
      unsubscribeLiveOpportunities();
      unsubscribeAnalysisStarted();
      unsubscribeAnalysisComplete();
      unsubscribeAnalysisError();
    };
  }, [serverUrl]);

  // Subscribe to specific game updates
  const subscribeToGame = useCallback((gameId) => {
    if (!subscribedGames.current.has(gameId)) {
      socketService.subscribeToGame(gameId);
      subscribedGames.current.add(gameId);
    }
  }, []);

  // Unsubscribe from game updates
  const unsubscribeFromGame = useCallback((gameId) => {
    if (subscribedGames.current.has(gameId)) {
      socketService.unsubscribeFromGame(gameId);
      subscribedGames.current.delete(gameId);
    }
  }, []);

  // Request AI analysis for a game
  const requestAnalysis = useCallback((gameId) => {
    socketService.requestAnalysis(gameId);
  }, []);

  // Get live opportunities
  const refreshOpportunities = useCallback(() => {
    socketService.getLiveOpportunities();
  }, []);

  // Get connection status
  const getConnectionStatus = useCallback(() => {
    return socketService.getConnectionStatus();
  }, []);

  return {
    // Connection state
    isConnected,
    connectionError,
    
    // Data state
    liveGames,
    liveOpportunities,
    gameAnalysis,
    analysisLoading,
    
    // Actions
    subscribeToGame,
    unsubscribeFromGame,
    requestAnalysis,
    refreshOpportunities,
    getConnectionStatus
  };
};

export default useSocket;
