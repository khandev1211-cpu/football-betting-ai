"""
Real-time Socket.IO Service for Live Betting Data
Handles WebSocket connections and real-time data streaming
"""

from flask_socketio import SocketIO, emit, join_room, leave_room
from flask import request
import threading
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from apscheduler.schedulers.background import BackgroundScheduler
import requests
from .probability_engine import ProbabilityEngine, LiveBettingAnalyzer
from .ai_analysis_service import AIAnalysisService

logger = logging.getLogger(__name__)

class RealtimeService:
    """Real-time data service with Socket.IO integration"""
    
    def __init__(self, socketio: SocketIO, odds_api_key: str, openai_api_key: str):
        self.socketio = socketio
        self.odds_api_key = odds_api_key
        self.ai_service = AIAnalysisService(openai_api_key)
        self.prob_engine = ProbabilityEngine()
        self.betting_analyzer = LiveBettingAnalyzer(self.prob_engine)
        
        # Active connections and subscriptions
        self.active_connections = {}
        self.game_subscriptions = {}
        self.live_games = {}
        
        # Background scheduler for data updates
        self.scheduler = BackgroundScheduler()
        self.scheduler.start()
        
        # Schedule periodic updates
        self.scheduler.add_job(
            func=self.update_live_games,
            trigger="interval",
            seconds=30,  # Update every 30 seconds
            id='live_games_update'
        )
        
        self.scheduler.add_job(
            func=self.update_odds_data,
            trigger="interval",
            seconds=60,  # Update odds every minute
            id='odds_update'
        )
        
        # Register Socket.IO event handlers
        self.register_socketio_handlers()
    
    def register_socketio_handlers(self):
        """Register all Socket.IO event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect():
            """Handle client connection"""
            client_id = request.sid
            self.active_connections[client_id] = {
                'connected_at': datetime.now(),
                'subscriptions': set()
            }
            
            logger.info(f"Client {client_id} connected")
            
            # Send initial data
            emit('connection_established', {
                'client_id': client_id,
                'server_time': datetime.now().isoformat(),
                'available_games': list(self.live_games.keys())
            })
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            client_id = request.sid
            if client_id in self.active_connections:
                # Clean up subscriptions
                subscriptions = self.active_connections[client_id]['subscriptions']
                for game_id in subscriptions:
                    if game_id in self.game_subscriptions:
                        self.game_subscriptions[game_id].discard(client_id)
                
                del self.active_connections[client_id]
                logger.info(f"Client {client_id} disconnected")
        
        @self.socketio.on('subscribe_game')
        def handle_subscribe_game(data):
            """Subscribe client to specific game updates"""
            client_id = request.sid
            game_id = data.get('game_id')
            
            if not game_id:
                emit('error', {'message': 'game_id is required'})
                return
            
            # Add to subscriptions
            if client_id in self.active_connections:
                self.active_connections[client_id]['subscriptions'].add(game_id)
            
            if game_id not in self.game_subscriptions:
                self.game_subscriptions[game_id] = set()
            self.game_subscriptions[game_id].add(client_id)
            
            join_room(f"game_{game_id}")
            
            # Send current game data if available
            if game_id in self.live_games:
                emit('game_update', {
                    'game_id': game_id,
                    'data': self.live_games[game_id]
                })
            
            logger.info(f"Client {client_id} subscribed to game {game_id}")
        
        @self.socketio.on('unsubscribe_game')
        def handle_unsubscribe_game(data):
            """Unsubscribe client from game updates"""
            client_id = request.sid
            game_id = data.get('game_id')
            
            if client_id in self.active_connections:
                self.active_connections[client_id]['subscriptions'].discard(game_id)
            
            if game_id in self.game_subscriptions:
                self.game_subscriptions[game_id].discard(client_id)
            
            leave_room(f"game_{game_id}")
            logger.info(f"Client {client_id} unsubscribed from game {game_id}")
        
        @self.socketio.on('request_analysis')
        def handle_analysis_request(data):
            """Handle AI analysis request for specific game"""
            client_id = request.sid
            game_id = data.get('game_id')
            
            if not game_id or game_id not in self.live_games:
                emit('error', {'message': 'Invalid game_id'})
                return
            
            # Perform AI analysis in background
            threading.Thread(
                target=self.perform_ai_analysis,
                args=(client_id, game_id)
            ).start()
            
            emit('analysis_started', {'game_id': game_id})
        
        @self.socketio.on('get_live_opportunities')
        def handle_live_opportunities():
            """Get current live betting opportunities"""
            opportunities = self.get_current_opportunities()
            emit('live_opportunities', opportunities)
    
    def update_live_games(self):
        """Update live games data from API"""
        try:
            # Fetch live games from The Odds API
            url = "https://api.the-odds-api.com/v4/sports/americanfootball_nfl/scores/"
            params = {
                'apiKey': self.odds_api_key,
                'daysFrom': 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                games_data = response.json()
                
                for game in games_data:
                    if game.get('completed', True):
                        continue  # Skip completed games
                    
                    game_id = game['id']
                    
                    # Update game data
                    updated_game = self.process_live_game_data(game)
                    
                    # Check if game data changed significantly
                    if self.game_data_changed(game_id, updated_game):
                        self.live_games[game_id] = updated_game
                        
                        # Broadcast update to subscribers
                        self.broadcast_game_update(game_id, updated_game)
                
                logger.info(f"Updated {len(self.live_games)} live games")
            
        except Exception as e:
            logger.error(f"Failed to update live games: {str(e)}")
    
    def update_odds_data(self):
        """Update odds data for live games using live API endpoint"""
        try:
            # Fetch all live odds with proper parameters
            live_odds_data = self.fetch_live_odds()
            
            for odds_data in live_odds_data:
                game_id = odds_data.get('game_id')
                if not game_id:
                    continue
                
                # Update or create game entry
                if game_id not in self.live_games:
                    self.live_games[game_id] = {
                        'game_id': game_id,
                        'home_team': odds_data.get('home_team'),
                        'away_team': odds_data.get('away_team'),
                        'commence_time': odds_data.get('commence_time'),
                        'is_live': self.is_game_live(odds_data.get('commence_time'))
                    }
                
                # Update odds data
                self.live_games[game_id]['odds_data'] = odds_data
                self.live_games[game_id]['last_odds_update'] = datetime.now().isoformat()
                
                # Broadcast odds update to subscribers
                self.broadcast_odds_update(game_id, odds_data)
            
            logger.info(f"Updated odds for {len(live_odds_data)} games")
        
        except Exception as e:
            logger.error(f"Failed to update odds data: {str(e)}")
    
    def is_game_live(self, commence_time: str) -> bool:
        """Check if game is currently live based on commence time"""
        if not commence_time:
            return False
        
        try:
            game_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
            now = datetime.now()
            
            # Game is live if it started within last 4 hours and hasn't been going for more than 4 hours
            return game_time <= now <= game_time + timedelta(hours=4)
        except:
            return False
    
    def process_live_game_data(self, raw_game_data: Dict) -> Dict:
        """Process raw game data into structured format"""
        game_data = {
            'game_id': raw_game_data['id'],
            'sport_key': raw_game_data.get('sport_key'),
            'sport_title': raw_game_data.get('sport_title'),
            'commence_time': raw_game_data.get('commence_time'),
            'home_team': raw_game_data.get('home_team'),
            'away_team': raw_game_data.get('away_team'),
            'completed': raw_game_data.get('completed', False),
            'last_update': datetime.now().isoformat()
        }
        
        # Process scores if available
        scores = raw_game_data.get('scores')
        if scores:
            for score in scores:
                team_name = score.get('name')
                if team_name == game_data['home_team']:
                    game_data['home_score'] = score.get('score', 0)
                elif team_name == game_data['away_team']:
                    game_data['away_score'] = score.get('score', 0)
        
        # Ensure scores are always present (default to 0 if missing)
        if 'home_score' not in game_data:
            game_data['home_score'] = 0
        if 'away_score' not in game_data:
            game_data['away_score'] = 0
            
        # Add derived statistics
        game_data['total_score'] = game_data['home_score'] + game_data['away_score']
        game_data['score_differential'] = abs(game_data['home_score'] - game_data['away_score'])
        
        # Ensure timing fields are always present
        if 'quarter' not in game_data:
            game_data['quarter'] = 1
        if 'minutes_remaining' not in game_data:
            game_data['minutes_remaining'] = 60.0
        if 'estimated_quarter' not in game_data:
            game_data['estimated_quarter'] = game_data.get('quarter', 1)
        if 'estimated_time_remaining' not in game_data:
            game_data['estimated_time_remaining'] = game_data.get('minutes_remaining', 60.0)
            
        # Estimate game progress (simplified)
        if not game_data['completed']:
            if 'estimated_quarter' not in game_data:
                game_data['estimated_quarter'] = self.estimate_quarter(game_data)
            if 'estimated_time_remaining' not in game_data:
                game_data['estimated_time_remaining'] = self.estimate_time_remaining(game_data)
        
        return game_data
    
    def fetch_live_odds(self, sport: str = 'americanfootball_nfl') -> List[Dict]:
        """Fetch live odds for all games using proper API parameters"""
        try:
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds"
            params = {
                'apiKey': self.odds_api_key,
                'regions': 'us',
                'markets': 'h2h,spreads,totals',
                'oddsFormat': 'american',
                'dateFormat': 'iso'
            }
            
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                odds_data = response.json()
                logger.info(f"Fetched odds for {len(odds_data)} games")
                return [self.process_odds_data(game_odds) for game_odds in odds_data]
            else:
                logger.error(f"Odds API error: {response.status_code} - {response.text}")
                return []
            
        except Exception as e:
            logger.error(f"Failed to fetch live odds: {str(e)}")
            return []
    
    def fetch_game_odds(self, game_id: str) -> Optional[Dict]:
        """Fetch current odds for a specific game"""
        try:
            # Get all live odds and filter for specific game
            all_odds = self.fetch_live_odds()
            
            for game_odds in all_odds:
                if game_odds.get('game_id') == game_id:
                    return game_odds
            
            return None
            
        except Exception as e:
            logger.error(f"Failed to fetch odds for game {game_id}: {str(e)}")
            return None
    
    def get_live_games_with_odds(self, sport: str = 'americanfootball_nfl') -> List[Dict]:
        """Get live games with current odds data"""
        try:
            live_odds = self.fetch_live_odds(sport)
            live_games_data = []
            
            for game_odds in live_odds:
                # Check if game is currently live
                commence_time = game_odds.get('commence_time')
                if commence_time:
                    game_time = datetime.fromisoformat(commence_time.replace('Z', '+00:00'))
                    now = datetime.now()
                    
                    # Consider game live if it started within last 4 hours
                    if game_time <= now <= game_time + timedelta(hours=4):
                        game_data = {
                            'game_id': game_odds['game_id'],
                            'home_team': game_odds.get('home_team'),
                            'away_team': game_odds.get('away_team'),
                            'commence_time': commence_time,
                            'is_live': True,
                            'odds_data': game_odds,
                            'last_update': datetime.now().isoformat()
                        }
                        live_games_data.append(game_data)
            
            logger.info(f"Found {len(live_games_data)} live games with odds")
            return live_games_data
            
        except Exception as e:
            logger.error(f"Failed to get live games with odds: {str(e)}")
            return []
    
    def process_odds_data(self, raw_odds: Dict) -> Dict:
        """Process raw odds data into structured format"""
        processed_odds = {
            'game_id': raw_odds['id'],
            'home_team': raw_odds.get('home_team'),
            'away_team': raw_odds.get('away_team'),
            'commence_time': raw_odds.get('commence_time'),
            'sport_key': raw_odds.get('sport_key'),
            'sport_title': raw_odds.get('sport_title'),
            'bookmakers': {},
            'best_odds': {},
            'timestamp': datetime.now().isoformat()
        }
        
        for bookmaker in raw_odds.get('bookmakers', []):
            book_name = bookmaker['title']
            processed_odds['bookmakers'][book_name] = {}
            
            for market in bookmaker.get('markets', []):
                market_key = market['key']
                processed_odds['bookmakers'][book_name][market_key] = {}
                
                for outcome in market.get('outcomes', []):
                    outcome_name = outcome['name']
                    processed_odds['bookmakers'][book_name][market_key][outcome_name] = {
                        'price': outcome.get('price'),
                        'point': outcome.get('point')
                    }
        
        # Calculate best odds across all books
        processed_odds['best_odds'] = self.find_best_odds(processed_odds['bookmakers'])
        
        return processed_odds
    
    def find_best_odds(self, bookmakers_odds: Dict) -> Dict:
        """Find best odds across all bookmakers"""
        best_odds = {}
        
        # Process each market type
        for book_name, book_odds in bookmakers_odds.items():
            for market_key, market_odds in book_odds.items():
                if market_key not in best_odds:
                    best_odds[market_key] = {}
                
                for outcome, odds_data in market_odds.items():
                    price = odds_data.get('price')
                    if price is None:
                        continue
                    
                    if outcome not in best_odds[market_key]:
                        best_odds[market_key][outcome] = {
                            'price': price,
                            'bookmaker': book_name,
                            'point': odds_data.get('point')
                        }
                    else:
                        # For positive odds, higher is better
                        # For negative odds, closer to 0 (less negative) is better
                        current_best = best_odds[market_key][outcome]['price']
                        
                        if (price > 0 and current_best > 0 and price > current_best) or \
                           (price < 0 and current_best < 0 and price > current_best) or \
                           (price > 0 and current_best < 0):
                            best_odds[market_key][outcome] = {
                                'price': price,
                                'bookmaker': book_name,
                                'point': odds_data.get('point')
                            }
        
        return best_odds
    
    def game_data_changed(self, game_id: str, new_data: Dict) -> bool:
        """Check if game data has changed significantly"""
        if game_id not in self.live_games:
            return True
        
        old_data = self.live_games[game_id]
        
        # Check for score changes
        if old_data.get('home_score') != new_data.get('home_score') or \
           old_data.get('away_score') != new_data.get('away_score'):
            return True
        
        # Check for quarter changes
        if old_data.get('estimated_quarter') != new_data.get('estimated_quarter'):
            return True
        
        return False
    
    def broadcast_game_update(self, game_id: str, game_data: Dict):
        """Broadcast game update to subscribed clients"""
        if game_id in self.game_subscriptions:
            self.socketio.emit('game_update', {
                'game_id': game_id,
                'data': game_data,
                'timestamp': datetime.now().isoformat()
            }, room=f"game_{game_id}")
            
            logger.info(f"Broadcasted update for game {game_id} to {len(self.game_subscriptions[game_id])} clients")
    
    def broadcast_odds_update(self, game_id: str, odds_data: Dict):
        """Broadcast odds update to subscribed clients"""
        if game_id in self.game_subscriptions:
            self.socketio.emit('odds_update', {
                'game_id': game_id,
                'odds_data': odds_data,
                'timestamp': datetime.now().isoformat()
            }, room=f"game_{game_id}")
    
    def perform_ai_analysis(self, client_id: str, game_id: str):
        """Perform AI analysis for a specific game"""
        try:
            if game_id not in self.live_games:
                return
            
            game_data = self.live_games[game_id]
            odds_data = game_data.get('odds_data', {})
            
            # Perform AI analysis
            analysis = self.ai_service.analyze_betting_edge(
                game_data,
                odds_data,
                f"Live analysis for {game_data.get('away_team')} @ {game_data.get('home_team')}"
            )
            
            # Send analysis to specific client
            self.socketio.emit('analysis_complete', {
                'game_id': game_id,
                'analysis': analysis,
                'timestamp': datetime.now().isoformat()
            }, room=client_id)
            
        except Exception as e:
            logger.error(f"AI analysis failed for game {game_id}: {str(e)}")
            self.socketio.emit('analysis_error', {
                'game_id': game_id,
                'error': str(e)
            }, room=client_id)
    
    def get_current_opportunities(self) -> Dict:
        """Get current betting opportunities across all live games"""
        opportunities = {
            'timestamp': datetime.now().isoformat(),
            'total_games': len(self.live_games),
            'opportunities': []
        }
        
        for game_id, game_data in self.live_games.items():
            odds_data = game_data.get('odds_data', {})
            if not odds_data:
                continue
            
            # Quick analysis for opportunities
            try:
                analysis = self.betting_analyzer.analyze_live_game(game_data, odds_data)
                
                for bet in analysis.get('best_bets', []):
                    if bet.get('expected_value', 0) > 0.03:  # 3% minimum edge
                        opportunities['opportunities'].append({
                            'game_id': game_id,
                            'game_info': f"{game_data.get('away_team')} @ {game_data.get('home_team')}",
                            'current_score': f"{game_data.get('away_score', 0)}-{game_data.get('home_score', 0)}",
                            **bet
                        })
            
            except Exception as e:
                logger.error(f"Failed to analyze opportunities for game {game_id}: {str(e)}")
        
        # Update total_games to reflect actual live games count
        opportunities['total_games'] = len(self.live_games)
        
        # Sort by expected value
        opportunities['opportunities'].sort(
            key=lambda x: x.get('expected_value', 0),
            reverse=True
        )
        
        return opportunities
    
    def estimate_quarter(self, game_data: Dict) -> int:
        """Estimate current quarter based on score and time"""
        # Simplified estimation - in real implementation, would use actual game clock
        total_score = game_data.get('total_score', 0)
        
        if total_score < 7:
            return 1
        elif total_score < 14:
            return 2
        elif total_score < 21:
            return 3
        else:
            return 4
    
    def estimate_time_remaining(self, game_data: Dict) -> float:
        """Estimate time remaining in game"""
        # Simplified estimation - in real implementation, would use actual game clock
        quarter = self.estimate_quarter(game_data)
        
        if quarter == 1:
            return 45.0  # Rough estimate
        elif quarter == 2:
            return 30.0
        elif quarter == 3:
            return 15.0
        else:
            return 5.0
    
    def _create_mock_opportunities(self) -> List[Dict]:
        """Create mock betting opportunities for demonstration when no live games available"""
        # Return empty list - no mock opportunities to avoid showing old/fake games
        return []

    def shutdown(self):
        """Shutdown the realtime service"""
        if self.scheduler.running:
            self.scheduler.shutdown()
        logger.info("Realtime service shutdown complete")
