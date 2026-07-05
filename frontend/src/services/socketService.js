/**
 * Socket.IO Service for Real-time Data Communication
 * Handles WebSocket connections and real-time betting data
 */

import { io } from 'socket.io-client';

class SocketService {
  constructor() {
    this.socket = null;
    this.isConnected = false;
    this.subscribers = new Map();
    this.reconnectAttempts = 0;
    this.maxReconnectAttempts = 5;
  }

  connect(serverUrl = 'http://localhost:5000') {
    if (this.socket && this.isConnected) {
      return this.socket;
    }

    this.socket = io(serverUrl, {
      transports: ['websocket', 'polling'],
      timeout: 20000,
      forceNew: true
    });

    this.setupEventHandlers();
    return this.socket;
  }

  setupEventHandlers() {
    this.socket.on('connect', () => {
      console.log('Socket.IO connected:', this.socket.id);
      this.isConnected = true;
      this.reconnectAttempts = 0;
      this.notifySubscribers('connection', { status: 'connected', socketId: this.socket.id });
    });

    this.socket.on('disconnect', (reason) => {
      console.log('Socket.IO disconnected:', reason);
      this.isConnected = false;
      this.notifySubscribers('connection', { status: 'disconnected', reason });
    });

    this.socket.on('connect_error', (error) => {
      console.error('Socket.IO connection error:', error);
      this.reconnectAttempts++;
      
      if (this.reconnectAttempts >= this.maxReconnectAttempts) {
        console.error('Max reconnection attempts reached');
        this.notifySubscribers('connection', { 
          status: 'error', 
          error: 'Max reconnection attempts reached' 
        });
      }
    });

    // Real-time betting data events
    this.socket.on('game_update', (data) => {
      console.log('Game update received:', data);
      this.notifySubscribers('game_update', data);
    });

    this.socket.on('odds_update', (data) => {
      console.log('Odds update received:', data);
      this.notifySubscribers('odds_update', data);
    });

    this.socket.on('live_opportunities', (data) => {
      console.log('Live opportunities received:', data);
      this.notifySubscribers('live_opportunities', data);
    });

    this.socket.on('analysis_complete', (data) => {
      console.log('Analysis complete:', data);
      this.notifySubscribers('analysis_complete', data);
    });

    this.socket.on('analysis_started', (data) => {
      console.log('Analysis started:', data);
      this.notifySubscribers('analysis_started', data);
    });

    this.socket.on('analysis_error', (data) => {
      console.error('Analysis error:', data);
      this.notifySubscribers('analysis_error', data);
    });

    this.socket.on('connection_established', (data) => {
      console.log('Connection established:', data);
      this.notifySubscribers('connection_established', data);
    });

    this.socket.on('error', (data) => {
      console.error('Socket error:', data);
      this.notifySubscribers('error', data);
    });
  }

  // Subscribe to specific events
  subscribe(event, callback) {
    if (!this.subscribers.has(event)) {
      this.subscribers.set(event, new Set());
    }
    this.subscribers.get(event).add(callback);

    // Return unsubscribe function
    return () => {
      const eventSubscribers = this.subscribers.get(event);
      if (eventSubscribers) {
        eventSubscribers.delete(callback);
      }
    };
  }

  // Notify all subscribers of an event
  notifySubscribers(event, data) {
    const eventSubscribers = this.subscribers.get(event);
    if (eventSubscribers) {
      eventSubscribers.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error('Error in subscriber callback:', error);
        }
      });
    }
  }

  // Game subscription methods
  subscribeToGame(gameId) {
    if (this.socket && this.isConnected) {
      this.socket.emit('subscribe_game', { game_id: gameId });
      console.log(`Subscribed to game: ${gameId}`);
    }
  }

  unsubscribeFromGame(gameId) {
    if (this.socket && this.isConnected) {
      this.socket.emit('unsubscribe_game', { game_id: gameId });
      console.log(`Unsubscribed from game: ${gameId}`);
    }
  }

  // Request AI analysis for a game
  requestAnalysis(gameId) {
    if (this.socket && this.isConnected) {
      this.socket.emit('request_analysis', { game_id: gameId });
      console.log(`Requested analysis for game: ${gameId}`);
    }
  }

  // Get current live opportunities
  getLiveOpportunities() {
    if (this.socket && this.isConnected) {
      this.socket.emit('get_live_opportunities');
      console.log('Requested live opportunities');
    }
  }

  // Disconnect socket
  disconnect() {
    if (this.socket) {
      this.socket.disconnect();
      this.socket = null;
      this.isConnected = false;
      console.log('Socket.IO disconnected manually');
    }
  }

  // Get connection status
  getConnectionStatus() {
    return {
      isConnected: this.isConnected,
      socketId: this.socket?.id || null,
      reconnectAttempts: this.reconnectAttempts
    };
  }
}

// Create singleton instance
const socketService = new SocketService();

export default socketService;
