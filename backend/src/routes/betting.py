"""
Betting API Routes
Handles endpoints for odds fetching, predictions, and EV calculations.
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import logging
from typing import Dict, List
from datetime import datetime

from ..services.enhanced_predictor import EnhancedFootballPredictor
from ..services.ev_calculator import EVCalculator
from ..services.api_fetcher import OddsFetcher

logger = logging.getLogger(__name__)

# Create blueprint
betting_bp = Blueprint('betting', __name__)

# Initialize services
predictor = EnhancedFootballPredictor()
ev_calculator = EVCalculator()
odds_fetcher = OddsFetcher()

@betting_bp.route('/odds', methods=['GET'])
@cross_origin()
def get_odds():
    """
    Get real-time odds for football games.
    
    Query Parameters:
        sport (str): Sport type ('nfl' or 'ncaaf'), default 'nfl'
        markets (str): Comma-separated markets ('moneyline,spread,totals')
        best_only (bool): Return only best odds across bookmakers
    
    Returns:
        JSON response with odds data
    """
    try:
        # Get query parameters
        sport = request.args.get('sport', 'nfl')
        markets_param = request.args.get('markets', 'moneyline,spread,totals')
        best_only = request.args.get('best_only', 'true').lower() == 'true'
        
        # Parse markets
        markets = [m.strip() for m in markets_param.split(',')]
        
        # Fetch odds
        odds_data = odds_fetcher.get_odds(sport=sport, markets=markets)
        
        if best_only:
            odds_data = odds_fetcher.get_best_odds(odds_data)
        
        return jsonify({
            'success': True,
            'data': odds_data,
            'count': len(odds_data),
            'sport': sport,
            'markets': markets
        })
        
    except Exception as e:
        logger.error(f"Error fetching odds: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@betting_bp.route('/odds/<game_id>', methods=['GET'])
@cross_origin()
def get_game_odds(game_id: str):
    """
    Get odds for a specific game.
    
    Args:
        game_id: Unique game identifier
    
    Returns:
        JSON response with game odds
    """
    try:
        sport = request.args.get('sport', 'nfl')
        
        game_odds = odds_fetcher.get_game_odds(game_id, sport)
        
        if not game_odds:
            return jsonify({
                'success': False,
                'error': 'Game not found'
            }), 404
        
        return jsonify({
            'success': True,
            'data': game_odds
        })
        
    except Exception as e:
        logger.error(f"Error fetching game odds: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@betting_bp.route('/predict', methods=['POST'])
@cross_origin()
def predict_game():
    """
    Generate predictions and EV calculations for a game.
    
    Request Body:
        {
            "game_data": {
                "home_team": "Kansas City Chiefs",
                "away_team": "Buffalo Bills",
                "game_id": "optional_game_id",
                // ... other game features
            },
            "odds_data": {
                "moneyline": {"home": -120, "away": +100},
                "spread": {"spread": -2.5, "home_odds": -110, "away_odds": -110},
                "total": {"total": 47.5, "over_odds": -110, "under_odds": -110}
            },
            "bankroll": 1000  // optional
        }
    
    Returns:
        JSON response with predictions and EV calculations
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        game_data = data.get('game_data', {})
        odds_data = data.get('odds_data', {})
        bankroll = data.get('bankroll', 1000)
        
        if not game_data:
            return jsonify({
                'success': False,
                'error': 'game_data is required'
            }), 400
        
        # Generate predictions
        predictions = predictor.predict_game(game_data)
        
        # Calculate EV if odds provided
        ev_results = {}
        betting_summary = {}
        
        if odds_data:
            ev_results = ev_calculator.calculate_all_markets_ev(predictions, odds_data)
            betting_summary = ev_calculator.generate_betting_summary(
                game_data, predictions, odds_data, bankroll
            )
        
        return jsonify({
            'success': True,
            'data': {
                'predictions': predictions,
                'ev_calculations': ev_results,
                'betting_summary': betting_summary,
                'game_info': {
                    'home_team': game_data.get('home_team'),
                    'away_team': game_data.get('away_team'),
                    'game_id': game_data.get('game_id')
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error generating predictions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@betting_bp.route('/predict/batch', methods=['POST'])
@cross_origin()
def predict_multiple_games():
    """
    Generate predictions for multiple games.
    
    Request Body:
        {
            "games": [
                {
                    "game_data": {...},
                    "odds_data": {...}
                },
                ...
            ],
            "bankroll": 1000
        }
    
    Returns:
        JSON response with predictions for all games
    """
    try:
        data = request.get_json()
        
        if not data or 'games' not in data:
            return jsonify({
                'success': False,
                'error': 'games array is required'
            }), 400
        
        games = data.get('games', [])
        bankroll = data.get('bankroll', 1000)
        
        results = []
        
        for game_info in games:
            try:
                game_data = game_info.get('game_data', {})
                odds_data = game_info.get('odds_data', {})
                
                # Generate predictions
                predictions = predictor.predict_game(game_data)
                
                # Calculate EV
                ev_results = {}
                betting_summary = {}
                
                if odds_data:
                    ev_results = ev_calculator.calculate_all_markets_ev(predictions, odds_data)
                    betting_summary = ev_calculator.generate_betting_summary(
                        game_data, predictions, odds_data, bankroll
                    )
                
                results.append({
                    'game_id': game_data.get('game_id', f"game_{len(results)}"),
                    'predictions': predictions,
                    'ev_calculations': ev_results,
                    'betting_summary': betting_summary
                })
                
            except Exception as e:
                logger.error(f"Error processing game: {str(e)}")
                results.append({
                    'game_id': game_info.get('game_data', {}).get('game_id', f"game_{len(results)}"),
                    'error': str(e)
                })
        
        return jsonify({
            'success': True,
            'data': results,
            'count': len(results)
        })
        
    except Exception as e:
        logger.error(f"Error processing batch predictions: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@betting_bp.route('/analyze', methods=['POST'])
@cross_origin()
def analyze_game_with_odds():
    """
    Comprehensive game analysis with live odds fetching.
    
    Request Body:
        {
            "game_id": "optional_game_id",
            "sport": "nfl",
            "game_data": {
                "home_team": "Kansas City Chiefs",
                "away_team": "Buffalo Bills",
                // ... other features
            },
            "bankroll": 1000
        }
    
    Returns:
        Complete analysis with predictions, live odds, and EV calculations
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        game_data = data.get('game_data', {})
        game_id = data.get('game_id')
        sport = data.get('sport', 'nfl')
        bankroll = data.get('bankroll', 1000)
        
        # Generate predictions
        predictions = predictor.predict_game(game_data)
        
        # Fetch live odds
        live_odds = None
        if game_id:
            live_odds = odds_fetcher.get_game_odds(game_id, sport)
        
        # If no specific game odds, get general odds for reference
        if not live_odds:
            all_odds = odds_fetcher.get_odds(sport)
            best_odds = odds_fetcher.get_best_odds(all_odds)
            
            # Try to match by team names
            home_team = game_data.get('home_team', '').lower()
            away_team = game_data.get('away_team', '').lower()
            
            for game in best_odds:
                if (home_team in game.get('home_team', '').lower() and 
                    away_team in game.get('away_team', '').lower()):
                    live_odds = game
                    break
        
        # Calculate EV with live odds
        ev_results = {}
        betting_summary = {}
        
        if live_odds and 'best_odds' in live_odds:
            odds_data = {
                'moneyline': live_odds['best_odds']['moneyline'],
                'spread': {
                    'spread': live_odds['best_odds']['spread']['line'],
                    'home_odds': live_odds['best_odds']['spread']['home'],
                    'away_odds': live_odds['best_odds']['spread']['away']
                },
                'total': {
                    'total': live_odds['best_odds']['totals']['line'],
                    'over_odds': live_odds['best_odds']['totals']['over'],
                    'under_odds': live_odds['best_odds']['totals']['under']
                }
            }
            
            ev_results = ev_calculator.calculate_all_markets_ev(predictions, odds_data)
            betting_summary = ev_calculator.generate_betting_summary(
                game_data, predictions, odds_data, bankroll
            )
            # Add live odds to betting summary for frontend display
            betting_summary['live_odds'] = live_odds
        
        return jsonify({
            'success': True,
            'data': {
                'predictions': predictions,
                'live_odds': live_odds,
                'ev_calculations': ev_results,
                'betting_summary': betting_summary,
                'analysis_timestamp': str(datetime.now()),
                'game_info': {
                    'home_team': game_data.get('home_team'),
                    'away_team': game_data.get('away_team'),
                    'sport': sport
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error analyzing game: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@betting_bp.route('/live', methods=['GET'])
@cross_origin()
def get_live_games():
    """
    Get live football games with current odds.
    
    Query Parameters:
        sport (str): Sport type ('nfl' or 'ncaaf'), default 'nfl'
        include_odds (bool): Include odds data, default 'true'
    
    Returns:
        JSON response with live games data
    """
    try:
        sport = request.args.get('sport', 'nfl')
        include_odds = request.args.get('include_odds', 'true').lower() == 'true'
        
        # Get live odds data (which includes live games)
        odds_data = odds_fetcher.get_odds(sport=sport)
        
        if not odds_data:
            return jsonify({
                'success': True,
                'data': [],
                'message': 'No live games available'
            })
        
        # Format response for live games
        live_games = []
        for game in odds_data:
            game_info = {
                'id': game.get('id'),
                'home_team': game.get('home_team'),
                'away_team': game.get('away_team'),
                'commence_time': game.get('commence_time'),
                'sport_key': game.get('sport_key')
            }
            
            if include_odds and 'bookmakers' in game:
                game_info['odds'] = game['bookmakers']
            
            live_games.append(game_info)
        
        return jsonify({
            'success': True,
            'data': live_games,
            'count': len(live_games)
        })
        
    except Exception as e:
        logger.error(f"Error fetching live games: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Failed to fetch live games: {str(e)}'
        }), 500

@betting_bp.route('/upcoming', methods=['GET'])
@cross_origin()
def get_upcoming_games():
    """
    Get upcoming games with odds and basic predictions.
    
    Query Parameters:
        sport (str): Sport type, default 'nfl'
        days (int): Days ahead to look, default 10 (changed from 7 to 10 per client request)
        include_predictions (bool): Include basic predictions, default false
    
    Returns:
        JSON response with upcoming games
    """
    try:
        sport = request.args.get('sport', 'nfl')
        days = int(request.args.get('days', 10))  # Changed default from 7 to 10 days
        include_predictions = request.args.get('include_predictions', 'false').lower() == 'true'
        
        # Get upcoming games with odds
        upcoming_games = odds_fetcher.get_upcoming_games(sport, days)
        
        # Add basic predictions if requested
        if include_predictions:
            for game in upcoming_games:
                try:
                    # Create basic game data from odds info
                    game_data = {
                        'home_team': game.get('home_team'),
                        'away_team': game.get('away_team'),
                        'game_id': game.get('id')
                    }
                    
                    # Generate basic predictions
                    predictions = predictor.predict_game(game_data)
                    game['predictions'] = predictions
                    
                except Exception as e:
                    logger.error(f"Error adding predictions for game {game.get('id')}: {str(e)}")
                    continue
        
        return jsonify({
            'success': True,
            'data': upcoming_games,
            'count': len(upcoming_games),
            'sport': sport,
            'days_ahead': days
        })
        
    except Exception as e:
        logger.error(f"Error fetching upcoming games: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@betting_bp.route('/sports', methods=['GET'])
@cross_origin()
def get_available_sports():
    """
    Get list of available sports.
    
    Returns:
        JSON response with available sports
    """
    try:
        sports = odds_fetcher.get_sports()
        
        return jsonify({
            'success': True,
            'data': sports
        })
        
    except Exception as e:
        logger.error(f"Error fetching sports: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@betting_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with service status
    """
    try:
        # Check if services are working
        status = {
            'predictor': len(predictor.models) > 0,
            'odds_fetcher': odds_fetcher.odds_api_key is not None,
            'ev_calculator': True
        }
        
        return jsonify({
            'success': True,
            'status': 'healthy',
            'services': status,
            'timestamp': str(datetime.now())
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'status': 'unhealthy',
            'error': str(e)
        }), 500

