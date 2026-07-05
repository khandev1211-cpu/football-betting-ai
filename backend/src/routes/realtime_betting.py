"""
Real-time Betting API Routes
Enhanced endpoints for live betting with AI analysis
"""

from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
import logging
from ..services.probability_engine import ProbabilityEngine, LiveBettingAnalyzer
from ..services.ai_analysis_service import AIAnalysisService
import os

logger = logging.getLogger(__name__)

realtime_betting_bp = Blueprint('realtime_betting', __name__)

# Initialize services
prob_engine = ProbabilityEngine()
betting_analyzer = LiveBettingAnalyzer(prob_engine)
ai_service = AIAnalysisService(os.getenv('OPENAI_API_KEY'))

@realtime_betting_bp.route('/live-games', methods=['GET'])
def get_live_games():
    """Get all currently live games with real-time data"""
    try:
        # This would typically fetch from your realtime service
        # For now, return mock data structure
        live_games = [
            {
                "game_id": "nfl_2024_week_1_buf_mia",
                "sport_key": "americanfootball_nfl",
                "sport_title": "NFL",
                "commence_time": "2024-09-08T17:00:00Z",
                "home_team": "Miami Dolphins",
                "away_team": "Buffalo Bills",
                "home_score": 14,
                "away_score": 21,
                "quarter": 3,
                "minutes_remaining": 8.5,
                "completed": False,
                "last_update": datetime.now().isoformat(),
                "home_team_stats": {
                    "off_epa_per_play": 0.12,
                    "def_epa_per_play_allowed": -0.08,
                    "red_zone_td_rate": 0.58,
                    "pace_seconds_per_play": 26.5,
                    "rating": 1650
                },
                "away_team_stats": {
                    "off_epa_per_play": 0.18,
                    "def_epa_per_play_allowed": -0.12,
                    "red_zone_td_rate": 0.62,
                    "pace_seconds_per_play": 25.8,
                    "rating": 1720
                }
            }
        ]
        
        return jsonify({
            "success": True,
            "data": live_games,
            "timestamp": datetime.now().isoformat(),
            "total_games": len(live_games)
        })
        
    except Exception as e:
        logger.error(f"Error fetching live games: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@realtime_betting_bp.route('/live-analysis/<game_id>', methods=['POST'])
def analyze_live_game(game_id):
    """Perform comprehensive AI analysis of live game"""
    try:
        data = request.get_json()
        game_data = data.get('game_data', {})
        odds_data = data.get('odds_data', {})
        
        # Perform AI analysis
        analysis = ai_service.analyze_betting_edge(
            game_data, 
            odds_data, 
            f"Live analysis for game {game_id}"
        )
        
        return jsonify({
            "success": True,
            "data": analysis,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error analyzing live game {game_id}: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@realtime_betting_bp.route('/live-opportunities', methods=['GET'])
def get_live_opportunities():
    """Get current live betting opportunities across all games"""
    try:
        # Mock live opportunities data
        opportunities = {
            "timestamp": datetime.now().isoformat(),
            "total_games": 3,
            "opportunities": [
                {
                    "game_id": "nfl_2024_week_1_buf_mia",
                    "game_info": "Buffalo Bills @ Miami Dolphins",
                    "current_score": "21-14",
                    "quarter": 3,
                    "time_remaining": 8.5,
                    "market": "total_under",
                    "bookmaker": "DraftKings",
                    "line": 47.5,
                    "odds": -108,
                    "your_probability": 0.68,
                    "implied_probability": 0.519,
                    "expected_value": 0.087,
                    "edge_percentage": 8.7,
                    "confidence": 0.75,
                    "recommendation": "GOOD_BET",
                    "kelly_fraction": 0.032,
                    "suggested_bet_size": "3.2% of bankroll"
                },
                {
                    "game_id": "nfl_2024_week_1_kc_det",
                    "game_info": "Kansas City Chiefs @ Detroit Lions",
                    "current_score": "10-17",
                    "quarter": 2,
                    "time_remaining": 12.3,
                    "market": "spread_underdog",
                    "bookmaker": "FanDuel",
                    "line": 3.5,
                    "odds": -110,
                    "your_probability": 0.58,
                    "implied_probability": 0.524,
                    "expected_value": 0.045,
                    "edge_percentage": 4.5,
                    "confidence": 0.65,
                    "recommendation": "CONSIDER",
                    "kelly_fraction": 0.018,
                    "suggested_bet_size": "1.8% of bankroll"
                }
            ]
        }
        
        return jsonify({
            "success": True,
            "data": opportunities
        })
        
    except Exception as e:
        logger.error(f"Error fetching live opportunities: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@realtime_betting_bp.route('/calculate-ev', methods=['POST'])
def calculate_expected_value():
    """Calculate Expected Value for specific betting scenario"""
    try:
        data = request.get_json()
        
        your_probability = data.get('your_probability')
        odds = data.get('odds')
        bet_amount = data.get('bet_amount', 100)
        
        if not all([your_probability, odds]):
            return jsonify({
                "success": False,
                "error": "your_probability and odds are required"
            }), 400
        
        # Calculate EV
        ev = prob_engine.calculate_expected_value(your_probability, odds, bet_amount)
        
        # Calculate other metrics
        implied_prob = prob_engine.calculate_implied_probability(odds)
        decimal_odds = prob_engine.calculate_decimal_odds(odds)
        
        # Kelly Criterion calculation
        if odds > 0:
            b = odds / 100
        else:
            b = 100 / abs(odds)
        
        kelly_fraction = (b * your_probability - (1 - your_probability)) / b
        safe_kelly = max(0, min(0.05, kelly_fraction * 0.25))  # 25% of Kelly, capped at 5%
        
        return jsonify({
            "success": True,
            "data": {
                "expected_value": ev,
                "expected_value_percentage": ev * 100,
                "your_probability": your_probability,
                "implied_probability": implied_prob,
                "decimal_odds": decimal_odds,
                "edge": your_probability - implied_prob,
                "edge_percentage": (your_probability - implied_prob) * 100,
                "kelly_fraction": kelly_fraction,
                "safe_kelly_fraction": safe_kelly,
                "recommended_bet_amount": bet_amount * safe_kelly if safe_kelly > 0 else 0,
                "recommendation": "BET" if ev > 0.03 else "PASS"
            }
        })
        
    except Exception as e:
        logger.error(f"Error calculating EV: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@realtime_betting_bp.route('/project-total', methods=['POST'])
def project_live_total():
    """Project final total for live game"""
    try:
        data = request.get_json()
        
        # Validate required fields
        required_fields = ['home_score', 'away_score', 'quarter', 'minutes_remaining']
        for field in required_fields:
            if field not in data:
                return jsonify({
                    "success": False,
                    "error": f"Missing required field: {field}"
                }), 400
        
        # Project total using probability engine
        projection = prob_engine.project_live_total(data)
        
        return jsonify({
            "success": True,
            "data": projection,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error projecting total: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@realtime_betting_bp.route('/analyze-over-under', methods=['POST'])
def analyze_over_under():
    """Analyze over/under betting opportunity"""
    try:
        data = request.get_json()
        
        projected_total = data.get('projected_total')
        line = data.get('line')
        over_odds = data.get('over_odds')
        under_odds = data.get('under_odds')
        
        if not all([projected_total, line, over_odds, under_odds]):
            return jsonify({
                "success": False,
                "error": "projected_total, line, over_odds, and under_odds are required"
            }), 400
        
        # Calculate probabilities
        probs = prob_engine.calculate_over_under_probabilities(projected_total, line)
        
        # Calculate EVs
        over_ev = prob_engine.calculate_expected_value(probs['prob_over'], over_odds)
        under_ev = prob_engine.calculate_expected_value(probs['prob_under'], under_odds)
        
        # Calculate vig
        vig = prob_engine.calculate_vig(over_odds, under_odds)
        
        # Determine best bet
        best_bet = None
        if over_ev > 0.03 and over_ev > under_ev:
            best_bet = {
                "side": "over",
                "odds": over_odds,
                "probability": probs['prob_over'],
                "expected_value": over_ev,
                "recommendation": "BET_OVER"
            }
        elif under_ev > 0.03:
            best_bet = {
                "side": "under", 
                "odds": under_odds,
                "probability": probs['prob_under'],
                "expected_value": under_ev,
                "recommendation": "BET_UNDER"
            }
        
        return jsonify({
            "success": True,
            "data": {
                "projected_total": projected_total,
                "line": line,
                "probabilities": probs,
                "over_analysis": {
                    "odds": over_odds,
                    "probability": probs['prob_over'],
                    "implied_probability": prob_engine.calculate_implied_probability(over_odds),
                    "expected_value": over_ev,
                    "edge_percentage": over_ev * 100
                },
                "under_analysis": {
                    "odds": under_odds,
                    "probability": probs['prob_under'],
                    "implied_probability": prob_engine.calculate_implied_probability(under_odds),
                    "expected_value": under_ev,
                    "edge_percentage": under_ev * 100
                },
                "market_analysis": {
                    "vig": vig,
                    "vig_percentage": vig * 100,
                    "fair_over_odds": prob_engine.calculate_decimal_odds(-100) if probs['prob_over'] == 0.5 else None,
                    "fair_under_odds": prob_engine.calculate_decimal_odds(-100) if probs['prob_under'] == 0.5 else None
                },
                "best_bet": best_bet,
                "recommendation": best_bet['recommendation'] if best_bet else "PASS"
            }
        })
        
    except Exception as e:
        logger.error(f"Error analyzing over/under: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@realtime_betting_bp.route('/health', methods=['GET'])
def health_check():
    """Health check for real-time betting service"""
    return jsonify({
        "success": True,
        "service": "realtime_betting",
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "features": [
            "live_games_tracking",
            "ai_powered_analysis", 
            "expected_value_calculations",
            "kelly_criterion_sizing",
            "real_time_projections"
        ]
    })

@realtime_betting_bp.route('/market-overview', methods=['GET'])
def get_market_overview():
    """Get AI-powered market overview"""
    try:
        # Mock market overview data
        overview = {
            "timestamp": datetime.now().isoformat(),
            "market_conditions": "FAVORABLE",
            "total_live_games": 8,
            "profitable_opportunities": 12,
            "average_edge": 4.2,
            "best_markets": ["totals", "live_spreads"],
            "ai_insights": "Current live betting environment shows strong value in under totals due to defensive adjustments in second half. Weather conditions in 3 games creating lower-scoring environments than projected.",
            "risk_factors": [
                "High variance in college games",
                "Weather impacts in outdoor venues",
                "Injury reports affecting key players"
            ],
            "recommended_focus": "Focus on NFL totals with 5%+ edges and avoid college spreads in blowout situations."
        }
        
        return jsonify({
            "success": True,
            "data": overview
        })
        
    except Exception as e:
        logger.error(f"Error generating market overview: {str(e)}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500
