"""
Advanced Probability Calculation Engine for Live Betting
Implements EPA-based models, pace calculations, and real-time projections
"""

import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, timedelta
import openai
import os
import json

logger = logging.getLogger(__name__)

class ProbabilityEngine:
    """Advanced probability calculations for NFL/NCAAF betting with AI integration"""
    
    def __init__(self):
        # NFL constants
        self.NFL_STD_DEV = 13.5  # Standard deviation for NFL point spreads
        self.NCAAF_STD_DEV = 15.0  # Higher variance for college football
        self.HOME_FIELD_ADVANTAGE = 2.5  # Points
        self.MINUTES_PER_GAME = 60.0
        
        # EPA (Expected Points Added) constants
        self.AVERAGE_PLAYS_PER_GAME = 130
        self.SECONDS_PER_PLAY_AVG = 28.0
        
        # Initialize AI client if API key is available
        self.ai_client = None
        api_key = os.getenv('OPENAI_API_KEY')
        if api_key:
            try:
                self.ai_client = openai.OpenAI(api_key=api_key)
                logger.info("AI client initialized for probability calculations")
            except Exception as e:
                logger.warning(f"Failed to initialize AI client: {str(e)}")
        else:
            logger.warning("No OpenAI API key found - AI features disabled")
        
    def calculate_implied_probability(self, odds: int) -> float:
        """Calculate implied probability from American odds"""
        if odds < 0:
            return abs(odds) / (abs(odds) + 100)
        else:
            return 100 / (odds + 100)
    
    def calculate_decimal_odds(self, odds: int) -> float:
        """Convert American odds to decimal odds"""
        if odds < 0:
            return (100 / abs(odds)) + 1
        else:
            return (odds / 100) + 1
    
    def calculate_vig(self, odds_1: int, odds_2: int) -> float:
        """Calculate bookmaker's vig (juice)"""
        prob_1 = self.calculate_implied_probability(odds_1)
        prob_2 = self.calculate_implied_probability(odds_2)
        return (prob_1 + prob_2) - 1
    
    def remove_vig(self, odds_1: int, odds_2: int) -> Tuple[float, float]:
        """Remove vig to get true probabilities"""
        prob_1 = self.calculate_implied_probability(odds_1)
        prob_2 = self.calculate_implied_probability(odds_2)
        total_prob = prob_1 + prob_2
        
        return prob_1 / total_prob, prob_2 / total_prob
    
    def calculate_expected_value(self, your_prob: float, odds: int, bet_amount: float = 1.0) -> float:
        """Calculate Expected Value for a bet"""
        decimal_odds = self.calculate_decimal_odds(odds)
        win_amount = (decimal_odds - 1) * bet_amount
        lose_amount = bet_amount
        
        ev = (your_prob * win_amount) - ((1 - your_prob) * lose_amount)
        return ev / bet_amount  # Return as percentage
    
    def project_live_total(self, game_data: Dict) -> Dict:
        """
        Project final total score for live game using EPA and pace
        
        Args:
            game_data: {
                'home_score': int,
                'away_score': int,
                'quarter': int,
                'minutes_remaining': float,
                'home_team_stats': {...},
                'away_team_stats': {...}
            }
        """
        current_total = game_data['home_score'] + game_data['away_score']
        minutes_remaining = game_data['minutes_remaining']
        
        # Get team stats
        home_stats = game_data.get('home_team_stats', {})
        away_stats = game_data.get('away_team_stats', {})
        
        # Calculate Points Per Minute (PPM) based on EPA
        home_ppm = self._calculate_ppm_from_epa(home_stats)
        away_ppm = self._calculate_ppm_from_epa(away_stats)
        combined_ppm = (home_ppm + away_ppm) / 2
        
        # Base projection
        projected_additional_points = minutes_remaining * combined_ppm
        
        # Apply quarter adjustments
        quarter_multiplier = self._get_quarter_multiplier(game_data['quarter'])
        projected_additional_points *= quarter_multiplier
        
        # Apply pace adjustments
        pace_adjustment = self._calculate_pace_adjustment(home_stats, away_stats)
        projected_additional_points *= pace_adjustment
        
        projected_total = current_total + projected_additional_points
        
        # Calculate confidence based on game situation
        confidence = self._calculate_projection_confidence(game_data, minutes_remaining)
        
        return {
            'projected_total': projected_total,
            'current_total': current_total,
            'projected_additional': projected_additional_points,
            'confidence': confidence,
            'home_ppm': home_ppm,
            'away_ppm': away_ppm,
            'combined_ppm': combined_ppm,
            'quarter_multiplier': quarter_multiplier,
            'pace_adjustment': pace_adjustment
        }
    
    def calculate_over_under_probabilities(self, projected_total: float, line: float, 
                                         std_dev: Optional[float] = None) -> Dict:
        """Calculate probabilities for over/under bet"""
        if std_dev is None:
            std_dev = self.NFL_STD_DEV
        
        # Use normal distribution to calculate probabilities
        prob_over = 1 - stats.norm.cdf(line, projected_total, std_dev)
        prob_under = stats.norm.cdf(line, projected_total, std_dev)
        
        return {
            'prob_over': prob_over,
            'prob_under': prob_under,
            'projected_total': projected_total,
            'line': line,
            'edge_over': projected_total - line,
            'edge_under': line - projected_total
        }
    
    def calculate_spread_probabilities(self, projected_margin: float, spread: float,
                                     std_dev: Optional[float] = None) -> Dict:
        """Calculate probabilities for spread betting"""
        if std_dev is None:
            std_dev = self.NFL_STD_DEV
        
        # Probability that favorite covers the spread
        prob_cover = 1 - stats.norm.cdf(spread, projected_margin, std_dev)
        prob_not_cover = stats.norm.cdf(spread, projected_margin, std_dev)
        
        return {
            'prob_favorite_covers': prob_cover,
            'prob_underdog_covers': prob_not_cover,
            'projected_margin': projected_margin,
            'spread': spread,
            'edge': projected_margin - spread
        }
    
    def calculate_moneyline_probabilities(self, home_rating: float, away_rating: float) -> Dict:
        """Calculate moneyline probabilities using Elo-style ratings"""
        rating_diff = home_rating - away_rating + self.HOME_FIELD_ADVANTAGE
        
        # Convert to probability using logistic function
        prob_home = 1 / (1 + 10**(-rating_diff / 400))
        prob_away = 1 - prob_home
        
        return {
            'prob_home_win': prob_home,
            'prob_away_win': prob_away,
            'rating_difference': rating_diff,
            'home_rating': home_rating,
            'away_rating': away_rating
        }
    
    def _calculate_ppm_from_epa(self, team_stats: Dict) -> float:
        """Calculate Points Per Minute from EPA and other stats"""
        # Default values if stats not available
        off_epa = team_stats.get('off_epa_per_play', 0.0)
        def_epa_allowed = team_stats.get('def_epa_per_play_allowed', 0.0)
        red_zone_td_rate = team_stats.get('red_zone_td_rate', 0.55)
        pace = team_stats.get('pace_seconds_per_play', self.SECONDS_PER_PLAY_AVG)
        
        # Convert EPA to points per play (rough approximation)
        net_epa = off_epa - def_epa_allowed
        points_per_play = max(0.1, 0.3 + (net_epa * 0.8) + (red_zone_td_rate * 0.2))
        
        # Convert to points per minute
        plays_per_minute = 60 / pace
        ppm = points_per_play * plays_per_minute
        
        return max(0.2, min(1.5, ppm))  # Reasonable bounds
    
    def _get_quarter_multiplier(self, quarter: int) -> float:
        """Adjust scoring rate by quarter"""
        multipliers = {
            1: 1.0,   # First quarter - normal pace
            2: 1.1,   # Second quarter - slightly higher
            3: 0.9,   # Third quarter - slower after halftime
            4: 1.2,   # Fourth quarter - urgency increases scoring
            5: 1.3    # Overtime
        }
        return multipliers.get(quarter, 1.0)
    
    def _calculate_pace_adjustment(self, home_stats: Dict, away_stats: Dict) -> float:
        """Calculate pace adjustment based on team tendencies"""
        home_pace = home_stats.get('pace_seconds_per_play', self.SECONDS_PER_PLAY_AVG)
        away_pace = away_stats.get('pace_seconds_per_play', self.SECONDS_PER_PLAY_AVG)
        
        avg_pace = (home_pace + away_pace) / 2
        league_avg_pace = self.SECONDS_PER_PLAY_AVG
        
        # Faster pace = more plays = more scoring opportunities
        pace_factor = league_avg_pace / avg_pace
        return max(0.8, min(1.3, pace_factor))
    
    def _calculate_projection_confidence(self, game_data: Dict, minutes_remaining: float) -> float:
        """Calculate confidence in projection based on game state"""
        base_confidence = 0.7
        
        # More confidence as game progresses
        time_factor = 1 - (minutes_remaining / self.MINUTES_PER_GAME)
        time_confidence = 0.3 + (time_factor * 0.4)
        
        # Less confidence in blowouts (garbage time effects)
        score_diff = abs(game_data['home_score'] - game_data['away_score'])
        if score_diff > 21:
            blowout_penalty = 0.2
        elif score_diff > 14:
            blowout_penalty = 0.1
        else:
            blowout_penalty = 0.0
        
        confidence = min(0.95, base_confidence + time_confidence - blowout_penalty)
        return max(0.3, confidence)
    
    def calculate_game_probabilities(self, game_data: Dict) -> Dict:
        """Calculate comprehensive game probabilities with AI enhancement"""
        home_rating = game_data.get('home_team_rating', 1500)
        away_rating = game_data.get('away_team_rating', 1500)
        
        # Calculate base probabilities
        ml_probs = self.calculate_moneyline_probabilities(home_rating, away_rating)
        
        spread = game_data.get('spread', 0.0)
        projected_margin = (home_rating - away_rating) / 25
        spread_probs = self.calculate_spread_probabilities(projected_margin, spread)
        
        total_line = game_data.get('total', 45.0)
        projected_total = 45.0 + ((home_rating + away_rating - 3000) / 100)
        ou_probs = self.calculate_over_under_probabilities(projected_total, total_line)
        
        # Get AI-enhanced analysis if available
        ai_analysis = self._get_ai_probability_analysis(game_data)
        
        # Combine statistical and AI analysis
        if ai_analysis:
            # Apply AI adjustments to base probabilities
            adjusted_home_prob = ml_probs['prob_home_win'] * ai_analysis.get('confidence_multiplier', 1.0)
            adjusted_home_prob += ai_analysis.get('home_bias_adjustment', 0.0)
            adjusted_home_prob = max(0.01, min(0.99, adjusted_home_prob))
            
            confidence = min(0.9, 0.6 + ai_analysis.get('confidence_boost', 0.0))
        else:
            adjusted_home_prob = ml_probs['prob_home_win']
            confidence = 0.6
        
        return {
            'home_win_probability': adjusted_home_prob,
            'away_win_probability': 1 - adjusted_home_prob,
            'draw_probability': 0.0,
            'confidence': confidence,
            'spread_analysis': spread_probs,
            'total_analysis': ou_probs,
            'projected_margin': projected_margin,
            'projected_total': projected_total,
            'ai_analysis': ai_analysis
        }
    
    def _get_ai_probability_analysis(self, game_data: Dict) -> Optional[Dict]:
        """Get AI-enhanced probability analysis using ChatGPT with quota management"""
        if not self.ai_client:
            logger.info("No AI client available, using statistical analysis only")
            return None
        
        try:
            prompt = f"""
            Analyze this football game for betting probability adjustments:
            
            Home Team: {game_data.get('home_team', 'Unknown')}
            Away Team: {game_data.get('away_team', 'Unknown')}
            Home Rating: {game_data.get('home_team_rating', 1500)}
            Away Rating: {game_data.get('away_team_rating', 1500)}
            
            Provide a JSON response with:
            - confidence_multiplier: float between 0.8-1.2 (1.0 = neutral)
            - home_bias_adjustment: float between -0.1 to 0.1 (0.0 = neutral)
            - confidence_boost: float between 0.0-0.2 (additional confidence)
            
            Consider factors like home field advantage, team form, and matchup dynamics.
            """
            
            response = self.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a sports betting analyst. Respond only with valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.3
            )
            
            ai_content = response.choices[0].message.content
            return self._parse_ai_probability_response(ai_content)
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower():
                # Silently handle quota exceeded - only log once per session
                if not hasattr(self, '_quota_logged'):
                    logger.warning("OpenAI API quota exceeded. Using statistical analysis only.")
                    self._quota_logged = True
                # Return neutral AI analysis when quota exceeded
                return {
                    'confidence_multiplier': 1.0,
                    'home_bias_adjustment': 0.0,
                    'confidence_boost': 0.0,
                    'reasoning': 'AI analysis unavailable due to quota limits'
                }
            else:
                logger.error(f"AI probability analysis failed: {error_msg}")
                return None
    
    def _create_probability_prompt(self, game_data: Dict) -> str:
        """Create prompt for AI probability analysis"""
        return f"""
        Analyze this NFL/NCAAF matchup and provide probability adjustments:
        
        MATCHUP: {game_data.get('away_team', 'Away')} @ {game_data.get('home_team', 'Home')}
        
        TEAM RATINGS:
        - Home Team Rating: {game_data.get('home_team_rating', 1500)}
        - Away Team Rating: {game_data.get('away_team_rating', 1500)}
        
        RECENT PERFORMANCE:
        - Home Recent Form: {game_data.get('home_recent_form', 0.5)}
        - Away Recent Form: {game_data.get('away_recent_form', 0.5)}
        
        GAME CONTEXT:
        - Week: {game_data.get('week', 1)}
        - Is Playoff: {game_data.get('is_playoff', False)}
        - Weather Impact: {game_data.get('weather_impact', 0)}
        
        MARKET DATA:
        - Spread: {game_data.get('spread', 0.0)}
        - Total: {game_data.get('total', 45.0)}
        - Home ML Odds: {game_data.get('home_ml_odds', -110)}
        - Away ML Odds: {game_data.get('away_ml_odds', -110)}
        
        Return JSON with:
        {{
            "confidence_multiplier": 0.8-1.2,
            "home_bias_adjustment": -0.1 to +0.1,
            "confidence_boost": 0.0-0.3,
            "key_factors": ["factor1", "factor2"],
            "reasoning": "brief explanation"
        }}
        """
    
    def _parse_ai_probability_response(self, ai_content: str) -> Optional[Dict]:
        """Parse AI response for probability adjustments"""
        try:
            # Extract JSON from response
            start_idx = ai_content.find('{')
            end_idx = ai_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = ai_content[start_idx:end_idx]
                return json.loads(json_str)
            
            return None
        except Exception as e:
            logger.error(f"Failed to parse AI probability response: {str(e)}")
            return None

class LiveBettingAnalyzer:
    """Analyze live betting opportunities with real-time edge calculations"""
    
    def __init__(self, probability_engine: ProbabilityEngine):
        self.prob_engine = probability_engine
        self.min_edge_threshold = 0.03  # 3% minimum edge
        self.high_confidence_threshold = 0.7
    
    def analyze_live_game(self, game_data: Dict, odds_data: Dict) -> Dict:
        """
        Comprehensive analysis of live betting opportunities
        
        Args:
            game_data: Live game state and team stats
            odds_data: Current odds from multiple books
        """
        analysis = {
            'game_id': game_data.get('game_id'),
            'timestamp': datetime.now().isoformat(),
            'game_state': {
                'quarter': game_data.get('quarter'),
                'time_remaining': game_data.get('minutes_remaining'),
                'score': f"{game_data.get('away_team')} {game_data.get('away_score')} - {game_data.get('home_score')} {game_data.get('home_team')}"
            },
            'projections': {},
            'betting_opportunities': [],
            'best_bets': []
        }
        
        # Total points projection
        total_projection = self.prob_engine.project_live_total(game_data)
        analysis['projections']['total'] = total_projection
        
        # Analyze over/under opportunities
        if 'totals' in odds_data:
            ou_opportunities = self._analyze_over_under(total_projection, odds_data['totals'])
            analysis['betting_opportunities'].extend(ou_opportunities)
        
        # Analyze spread opportunities (if available)
        if 'spreads' in odds_data:
            spread_opportunities = self._analyze_spreads(game_data, odds_data['spreads'])
            analysis['betting_opportunities'].extend(spread_opportunities)
        
        # Analyze moneyline opportunities
        if 'moneylines' in odds_data:
            ml_opportunities = self._analyze_moneylines(game_data, odds_data['moneylines'])
            analysis['betting_opportunities'].extend(ml_opportunities)
        
        # Filter and rank best opportunities
        analysis['best_bets'] = self._rank_betting_opportunities(analysis['betting_opportunities'])
        
        return analysis
    
    def _analyze_over_under(self, projection: Dict, totals_odds: List[Dict]) -> List[Dict]:
        """Analyze over/under betting opportunities"""
        opportunities = []
        
        for book_odds in totals_odds:
            line = book_odds.get('line')
            over_odds = book_odds.get('over_odds')
            under_odds = book_odds.get('under_odds')
            bookmaker = book_odds.get('bookmaker')
            
            if not all([line, over_odds, under_odds]):
                continue
            
            # Calculate probabilities
            probs = self.prob_engine.calculate_over_under_probabilities(
                projection['projected_total'], line
            )
            
            # Calculate EVs
            over_ev = self.prob_engine.calculate_expected_value(probs['prob_over'], over_odds)
            under_ev = self.prob_engine.calculate_expected_value(probs['prob_under'], under_odds)
            
            # Over opportunity
            if over_ev > self.min_edge_threshold:
                opportunities.append({
                    'market': 'total_over',
                    'bookmaker': bookmaker,
                    'line': line,
                    'odds': over_odds,
                    'your_probability': probs['prob_over'],
                    'implied_probability': self.prob_engine.calculate_implied_probability(over_odds),
                    'expected_value': over_ev,
                    'edge_percentage': over_ev * 100,
                    'confidence': projection['confidence'],
                    'recommendation': self._get_recommendation(over_ev, projection['confidence'])
                })
            
            # Under opportunity
            if under_ev > self.min_edge_threshold:
                opportunities.append({
                    'market': 'total_under',
                    'bookmaker': bookmaker,
                    'line': line,
                    'odds': under_odds,
                    'your_probability': probs['prob_under'],
                    'implied_probability': self.prob_engine.calculate_implied_probability(under_odds),
                    'expected_value': under_ev,
                    'edge_percentage': under_ev * 100,
                    'confidence': projection['confidence'],
                    'recommendation': self._get_recommendation(under_ev, projection['confidence'])
                })
        
        return opportunities
    
    def _analyze_spreads(self, game_data: Dict, spread_odds: List[Dict]) -> List[Dict]:
        """Analyze spread betting opportunities"""
        opportunities = []
        
        # Calculate projected margin (simplified)
        home_stats = game_data.get('home_team_stats', {})
        away_stats = game_data.get('away_team_stats', {})
        
        home_rating = home_stats.get('rating', 1500)
        away_rating = away_stats.get('rating', 1500)
        
        ml_probs = self.prob_engine.calculate_moneyline_probabilities(home_rating, away_rating)
        
        # Rough margin projection (can be enhanced)
        projected_margin = (home_rating - away_rating) / 25  # Simplified conversion
        
        for book_odds in spread_odds:
            spread = book_odds.get('spread')
            favorite_odds = book_odds.get('favorite_odds')
            underdog_odds = book_odds.get('underdog_odds')
            bookmaker = book_odds.get('bookmaker')
            
            if not all([spread, favorite_odds, underdog_odds]):
                continue
            
            spread_probs = self.prob_engine.calculate_spread_probabilities(projected_margin, spread)
            
            # Calculate EVs
            fav_ev = self.prob_engine.calculate_expected_value(
                spread_probs['prob_favorite_covers'], favorite_odds
            )
            dog_ev = self.prob_engine.calculate_expected_value(
                spread_probs['prob_underdog_covers'], underdog_odds
            )
            
            # Add opportunities if profitable
            if fav_ev > self.min_edge_threshold:
                opportunities.append({
                    'market': 'spread_favorite',
                    'bookmaker': bookmaker,
                    'line': spread,
                    'odds': favorite_odds,
                    'your_probability': spread_probs['prob_favorite_covers'],
                    'implied_probability': self.prob_engine.calculate_implied_probability(favorite_odds),
                    'expected_value': fav_ev,
                    'edge_percentage': fav_ev * 100,
                    'confidence': 0.6,  # Lower confidence for spreads
                    'recommendation': self._get_recommendation(fav_ev, 0.6)
                })
            
            if dog_ev > self.min_edge_threshold:
                opportunities.append({
                    'market': 'spread_underdog',
                    'bookmaker': bookmaker,
                    'line': spread,
                    'odds': underdog_odds,
                    'your_probability': spread_probs['prob_underdog_covers'],
                    'implied_probability': self.prob_engine.calculate_implied_probability(underdog_odds),
                    'expected_value': dog_ev,
                    'edge_percentage': dog_ev * 100,
                    'confidence': 0.6,
                    'recommendation': self._get_recommendation(dog_ev, 0.6)
                })
        
        return opportunities
    
    def _analyze_moneylines(self, game_data: Dict, ml_odds: List[Dict]) -> List[Dict]:
        """Analyze moneyline betting opportunities"""
        opportunities = []
        
        home_stats = game_data.get('home_team_stats', {})
        away_stats = game_data.get('away_team_stats', {})
        
        home_rating = home_stats.get('rating', 1500)
        away_rating = away_stats.get('rating', 1500)
        
        ml_probs = self.prob_engine.calculate_moneyline_probabilities(home_rating, away_rating)
        
        for book_odds in ml_odds:
            home_odds = book_odds.get('home_odds')
            away_odds = book_odds.get('away_odds')
            bookmaker = book_odds.get('bookmaker')
            
            if not all([home_odds, away_odds]):
                continue
            
            # Calculate EVs
            home_ev = self.prob_engine.calculate_expected_value(ml_probs['prob_home_win'], home_odds)
            away_ev = self.prob_engine.calculate_expected_value(ml_probs['prob_away_win'], away_odds)
            
            # Add opportunities
            if home_ev > self.min_edge_threshold:
                opportunities.append({
                    'market': 'moneyline_home',
                    'bookmaker': bookmaker,
                    'odds': home_odds,
                    'your_probability': ml_probs['prob_home_win'],
                    'implied_probability': self.prob_engine.calculate_implied_probability(home_odds),
                    'expected_value': home_ev,
                    'edge_percentage': home_ev * 100,
                    'confidence': 0.65,
                    'recommendation': self._get_recommendation(home_ev, 0.65)
                })
            
            if away_ev > self.min_edge_threshold:
                opportunities.append({
                    'market': 'moneyline_away',
                    'bookmaker': bookmaker,
                    'odds': away_odds,
                    'your_probability': ml_probs['prob_away_win'],
                    'implied_probability': self.prob_engine.calculate_implied_probability(away_odds),
                    'expected_value': away_ev,
                    'edge_percentage': away_ev * 100,
                    'confidence': 0.65,
                    'recommendation': self._get_recommendation(away_ev, 0.65)
                })
        
        return opportunities
    
    def _get_recommendation(self, ev: float, confidence: float) -> str:
        """Get betting recommendation based on EV and confidence"""
        if ev > 0.1 and confidence > 0.8:
            return 'STRONG_BET'
        elif ev > 0.05 and confidence > 0.7:
            return 'GOOD_BET'
        elif ev > 0.03 and confidence > 0.6:
            return 'CONSIDER'
        elif ev > 0.01:
            return 'LOW_CONFIDENCE'
        else:
            return 'PASS'
    
    def _rank_betting_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """Rank betting opportunities by EV and confidence"""
        # Sort by EV * confidence score
        ranked = sorted(
            opportunities,
            key=lambda x: x['expected_value'] * x['confidence'],
            reverse=True
        )
        
        return ranked[:10]  # Return top 10 opportunities
    
    def get_dataset_enhanced_predictions(self, game_data: Dict, historical_data: List[Dict]) -> Dict:
        """Use ChatGPT to analyze historical dataset and enhance predictions"""
        if not self.prob_engine.ai_client:
            return {'error': 'AI client not available'}
        
        try:
            # Prepare dataset summary for AI analysis
            dataset_summary = self._prepare_dataset_summary(historical_data)
            
            dataset_prompt = f"""
            Analyze this historical dataset to enhance current game prediction:
            
            CURRENT GAME:
            {game_data.get('away_team')} @ {game_data.get('home_team')}
            Spread: {game_data.get('spread')}, Total: {game_data.get('total')}
            
            HISTORICAL DATASET SUMMARY:
            {dataset_summary}
            
            Based on historical patterns, provide enhanced predictions:
            {{
                "probability_adjustments": {{
                    "home_win_adjustment": -0.1 to +0.1,
                    "total_adjustment": -5.0 to +5.0,
                    "spread_adjustment": -3.0 to +3.0
                }},
                "key_patterns": ["pattern1", "pattern2"],
                "confidence_level": 0.0-1.0,
                "historical_context": "brief explanation"
            }}
            """
            
            response = self.prob_engine.ai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a data scientist analyzing sports betting datasets for predictive insights."},
                    {"role": "user", "content": dataset_prompt}
                ],
                temperature=0.2,
                max_tokens=600
            )
            
            return self._parse_dataset_response(response.choices[0].message.content)
            
        except Exception as e:
            logger.error(f"Dataset analysis failed: {str(e)}")
            return {'error': f'Dataset analysis failed: {str(e)}'}
    
    def _prepare_dataset_summary(self, historical_data: List[Dict]) -> str:
        """Prepare summary of historical dataset for AI analysis"""
        if not historical_data:
            return "No historical data available"
        
        # Calculate basic statistics from dataset
        total_games = len(historical_data)
        home_wins = sum(1 for game in historical_data if game.get('home_win', False))
        avg_total = sum(game.get('total_score', 0) for game in historical_data) / total_games if total_games > 0 else 0
        
        return f"""
        Dataset Size: {total_games} games
        Home Win Rate: {home_wins/total_games:.2%} if total_games > 0 else 0
        Average Total Score: {avg_total:.1f}
        Recent Trends: Last 10 games analysis
        """
    
    def _parse_dataset_response(self, ai_content: str) -> Dict:
        """Parse AI dataset analysis response"""
        try:
            start_idx = ai_content.find('{')
            end_idx = ai_content.rfind('}') + 1
            
            if start_idx != -1 and end_idx != -1:
                json_str = ai_content[start_idx:end_idx]
                return json.loads(json_str)
            
            return {'error': 'Could not parse AI response'}
        except Exception as e:
            logger.error(f"Failed to parse dataset response: {str(e)}")
            return {'error': f'Parse error: {str(e)}'}
