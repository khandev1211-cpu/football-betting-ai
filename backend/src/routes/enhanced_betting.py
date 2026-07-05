"""
Enhanced Betting API Routes with Advanced EV Calculations
Implements client's requested sophisticated edge detection and AI analysis.
"""

from flask import Blueprint, request, jsonify
from flask_cors import cross_origin
import logging
import asyncio
from typing import Dict, List
from datetime import datetime

from src.services.advanced_ev_calculator import AdvancedEVCalculator
from src.services.live_betting_engine import LiveBettingEngine
from src.services.api_fetcher import OddsFetcher

logger = logging.getLogger(__name__)

# Create blueprint
enhanced_betting_bp = Blueprint('enhanced_betting', __name__)

# Initialize services
advanced_ev_calculator = AdvancedEVCalculator()
live_betting_engine = LiveBettingEngine()
odds_fetcher = OddsFetcher()

@enhanced_betting_bp.route('/advanced-analysis', methods=['POST'])
@cross_origin()
def advanced_game_analysis():
    """
    Perform advanced betting analysis with sophisticated EV calculations.
    
    Request Body:
        {
            "game_data": {
                "home_team": "Miami Dolphins",
                "away_team": "New England Patriots",
                "home_team_rating": 1580,
                "away_team_rating": 1520,
                "home_off_epa_per_play": 0.05,
                "away_off_epa_per_play": -0.02,
                "home_def_epa_per_play": -0.03,
                "away_def_epa_per_play": 0.01,
                "home_field_advantage": 3.0,
                "weather_impact": -1.5
            },
            "odds_data": {
                "moneyline": {"home": -150, "away": +130},
                "spread": {"spread": -3.5, "home_odds": -110, "away_odds": -110},
                "total": {"total": 47.5, "over_odds": -110, "under_odds": -110}
            },
            "include_ai_analysis": true
        }
    
    Returns:
        Comprehensive analysis with advanced EV calculations
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
        include_ai = data.get('include_ai_analysis', False)
        
        if not game_data or not odds_data:
            return jsonify({
                'success': False,
                'error': 'Both game_data and odds_data are required'
            }), 400
        
        # Perform comprehensive analysis
        analysis = advanced_ev_calculator.comprehensive_game_analysis(game_data, odds_data)
        
        # Add AI analysis if requested
        ai_analysis = None
        if include_ai:
            try:
                # Use asyncio to handle async AI analysis
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                ai_analysis = loop.run_until_complete(
                    advanced_ev_calculator.get_ai_analysis(game_data, analysis.get('summary', {}))
                )
                loop.close()
            except Exception as e:
                logger.error(f"AI analysis failed: {str(e)}")
                ai_analysis = "AI analysis unavailable"
        
        return jsonify({
            'success': True,
            'data': {
                'analysis': analysis,
                'ai_insights': ai_analysis,
                'calculation_method': 'advanced_ev_with_epa',
                'timestamp': datetime.now().isoformat()
            }
        })
        
    except Exception as e:
        logger.error(f"Error in advanced analysis: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_betting_bp.route('/live-edge-calculation', methods=['POST'])
@cross_origin()
def calculate_live_edge():
    """
    Calculate betting edge for live games with real-time projections.
    
    Request Body:
        {
            "game_state": {
                "game_id": "NE@MIA-2025-01-15",
                "home_team": "Miami Dolphins",
                "away_team": "New England Patriots",
                "home_score": 14,
                "away_score": 10,
                "quarter": 2,
                "clock": "8:30",
                "minutes_remaining": 38.5,
                "home_ppm_estimate": 0.68,
                "away_ppm_estimate": 0.61
            },
            "current_odds": {
                "total": {"total": 45.5, "over_odds": -105, "under_odds": -115},
                "spread": {"spread": -2.5, "home_odds": -110, "away_odds": -110}
            }
        }
    
    Returns:
        Live betting edge analysis with projections
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        game_state = data.get('game_state', {})
        current_odds = data.get('current_odds', {})
        
        if not game_state or not current_odds:
            return jsonify({
                'success': False,
                'error': 'Both game_state and current_odds are required'
            }), 400
        
        # Update live game state
        live_game_state = live_betting_engine.update_game_state(game_state)
        
        # Calculate live edge
        game_id = game_state.get('game_id')
        analysis = live_betting_engine.calculate_live_edge(game_id, current_odds)
        
        if not analysis:
            return jsonify({
                'success': False,
                'error': 'Could not calculate live edge'
            }), 400
        
        # Check for betting opportunities
        alerts = live_betting_engine.check_betting_opportunities(game_id)
        
        return jsonify({
            'success': True,
            'data': {
                'live_analysis': analysis,
                'betting_alerts': [
                    {
                        'market': alert.market,
                        'ev_percentage': alert.ev_percentage,
                        'recommendation': alert.recommendation,
                        'confidence': alert.confidence,
                        'message': alert.message
                    }
                    for alert in alerts
                ],
                'game_state_summary': {
                    'current_score': f"{live_game_state.away_score}-{live_game_state.home_score}",
                    'time_remaining': live_game_state.minutes_remaining,
                    'quarter': live_game_state.quarter
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating live edge: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_betting_bp.route('/implied-probability', methods=['POST'])
@cross_origin()
def calculate_implied_probabilities():
    """
    Calculate implied probabilities and remove vig from odds.
    
    Request Body:
        {
            "odds": {
                "over": -110,
                "under": -105
            }
        }
    
    Returns:
        Implied probabilities with and without vig
    """
    try:
        data = request.get_json()
        
        if not data or 'odds' not in data:
            return jsonify({
                'success': False,
                'error': 'Odds data required'
            }), 400
        
        odds = data['odds']
        
        if 'over' in odds and 'under' in odds:
            # Total odds
            over_odds = odds['over']
            under_odds = odds['under']
            
            implied_over = advanced_ev_calculator.calculate_implied_probability(over_odds)
            implied_under = advanced_ev_calculator.calculate_implied_probability(under_odds)
            
            no_vig_over, no_vig_under, vig = advanced_ev_calculator.calculate_no_vig_probability(
                over_odds, under_odds
            )
            
            return jsonify({
                'success': True,
                'data': {
                    'implied_probabilities': {
                        'over': implied_over,
                        'under': implied_under,
                        'total': implied_over + implied_under
                    },
                    'no_vig_probabilities': {
                        'over': no_vig_over,
                        'under': no_vig_under
                    },
                    'vig_percentage': vig * 100,
                    'decimal_odds': {
                        'over': advanced_ev_calculator.calculate_decimal_odds(over_odds),
                        'under': advanced_ev_calculator.calculate_decimal_odds(under_odds)
                    }
                }
            })
        
        elif 'home' in odds and 'away' in odds:
            # Moneyline odds
            home_odds = odds['home']
            away_odds = odds['away']
            
            implied_home = advanced_ev_calculator.calculate_implied_probability(home_odds)
            implied_away = advanced_ev_calculator.calculate_implied_probability(away_odds)
            
            total_implied = implied_home + implied_away
            vig = total_implied - 1
            
            no_vig_home = implied_home / total_implied
            no_vig_away = implied_away / total_implied
            
            return jsonify({
                'success': True,
                'data': {
                    'implied_probabilities': {
                        'home': implied_home,
                        'away': implied_away,
                        'total': total_implied
                    },
                    'no_vig_probabilities': {
                        'home': no_vig_home,
                        'away': no_vig_away
                    },
                    'vig_percentage': vig * 100,
                    'decimal_odds': {
                        'home': advanced_ev_calculator.calculate_decimal_odds(home_odds),
                        'away': advanced_ev_calculator.calculate_decimal_odds(away_odds)
                    }
                }
            })
        
        else:
            return jsonify({
                'success': False,
                'error': 'Invalid odds format. Provide either over/under or home/away odds.'
            }), 400
        
    except Exception as e:
        logger.error(f"Error calculating implied probabilities: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_betting_bp.route('/ev-calculator', methods=['POST'])
@cross_origin()
def calculate_expected_value():
    """
    Calculate Expected Value for specific betting scenarios.
    
    Request Body:
        {
            "your_probability": 0.61,
            "odds": -105,
            "bet_amount": 100
        }
    
    Returns:
        Expected Value calculation with detailed breakdown
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        your_prob = data.get('your_probability')
        odds = data.get('odds')
        bet_amount = data.get('bet_amount', 100)
        
        if your_prob is None or odds is None:
            return jsonify({
                'success': False,
                'error': 'your_probability and odds are required'
            }), 400
        
        # Calculate EV
        ev = advanced_ev_calculator.calculate_ev(your_prob, odds)
        
        # Calculate additional metrics
        implied_prob = advanced_ev_calculator.calculate_implied_probability(odds)
        decimal_odds = advanced_ev_calculator.calculate_decimal_odds(odds)
        
        # Calculate potential profit/loss
        if odds > 0:
            potential_profit = bet_amount * (odds / 100)
        else:
            potential_profit = bet_amount * (100 / abs(odds))
        
        expected_profit = ev * bet_amount
        
        # Edge calculation
        edge = your_prob - implied_prob
        edge_percentage = edge * 100
        
        return jsonify({
            'success': True,
            'data': {
                'expected_value': ev,
                'ev_percentage': ev * 100,
                'expected_profit': expected_profit,
                'edge': edge,
                'edge_percentage': edge_percentage,
                'recommendation': advanced_ev_calculator.get_recommendation(ev),
                'bet_details': {
                    'bet_amount': bet_amount,
                    'potential_profit': potential_profit,
                    'potential_loss': bet_amount,
                    'your_probability': your_prob,
                    'implied_probability': implied_prob,
                    'decimal_odds': decimal_odds
                },
                'risk_assessment': {
                    'win_probability': your_prob,
                    'lose_probability': 1 - your_prob,
                    'expected_return': (your_prob * (bet_amount + potential_profit)) + 
                                     ((1 - your_prob) * 0)
                }
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating EV: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_betting_bp.route('/live-monitoring/start', methods=['POST'])
@cross_origin()
def start_live_monitoring():
    """
    Start monitoring live games for betting opportunities.
    
    Request Body:
        {
            "game_ids": ["NE@MIA-2025-01-15", "BUF@NYJ-2025-01-15"],
            "min_ev_threshold": 0.03,
            "check_interval": 30
        }
    
    Returns:
        Monitoring status
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        game_ids = data.get('game_ids', [])
        min_ev_threshold = data.get('min_ev_threshold', 0.03)
        check_interval = data.get('check_interval', 30)
        
        if not game_ids:
            return jsonify({
                'success': False,
                'error': 'game_ids required'
            }), 400
        
        # Update monitoring settings
        live_betting_engine.min_ev_threshold = min_ev_threshold
        
        # Start monitoring (in a real implementation, this would be handled differently)
        # For now, we'll just acknowledge the request
        
        return jsonify({
            'success': True,
            'data': {
                'monitoring_started': True,
                'game_ids': game_ids,
                'min_ev_threshold': min_ev_threshold,
                'check_interval': check_interval,
                'message': 'Live monitoring configured. In production, this would start background monitoring.'
            }
        })
        
    except Exception as e:
        logger.error(f"Error starting live monitoring: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_betting_bp.route('/simulation/live-update', methods=['POST'])
@cross_origin()
def simulate_live_update():
    """
    Simulate a live game update for testing purposes.
    
    Request Body:
        {
            "game_id": "NE@MIA-2025-01-15",
            "score_update": {
                "home_score": 21,
                "away_score": 10,
                "quarter": 3,
                "minutes_remaining": 30.0
            }
        }
    
    Returns:
        Updated analysis and any generated alerts
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'No data provided'
            }), 400
        
        game_id = data.get('game_id')
        score_update = data.get('score_update', {})
        
        if not game_id or not score_update:
            return jsonify({
                'success': False,
                'error': 'game_id and score_update are required'
            }), 400
        
        # Simulate the update
        result = live_betting_engine.simulate_live_game_update(game_id, score_update)
        
        return jsonify({
            'success': True,
            'data': result
        })
        
    except Exception as e:
        logger.error(f"Error simulating live update: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@enhanced_betting_bp.route('/active-games', methods=['GET'])
@cross_origin()
def get_active_games():
    """
    Get summary of all active live games being monitored.
    
    Returns:
        Dictionary of active games with current status
    """
    try:
        active_games = live_betting_engine.get_active_games()
        
        return jsonify({
            'success': True,
            'data': {
                'active_games': active_games,
                'total_games': len(active_games),
                'monitoring_status': live_betting_engine.is_monitoring
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting active games: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
