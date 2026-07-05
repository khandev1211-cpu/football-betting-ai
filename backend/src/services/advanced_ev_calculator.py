"""
Advanced Expected Value Calculator with Enhanced Edge Detection
Implements sophisticated betting edge calculations as requested by client.
"""

import os
import numpy as np
import pandas as pd
from scipy import stats
from typing import Dict, List, Tuple, Optional
import logging
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

class AdvancedEVCalculator:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
    def calculate_implied_probability(self, odds: int) -> float:
        """
        Calculate implied probability from American odds.
        
        Args:
            odds: American odds (e.g., -110, +105)
            
        Returns:
            Implied probability as decimal
        """
        if odds < 0:
            return abs(odds) / (abs(odds) + 100)
        else:
            return 100 / (odds + 100)
    
    def calculate_no_vig_probability(self, odds_over: int, odds_under: int) -> Tuple[float, float]:
        """
        Remove vig (bookmaker margin) to get true probabilities.
        
        Args:
            odds_over: Over odds (American format)
            odds_under: Under odds (American format)
            
        Returns:
            Tuple of (no_vig_prob_over, no_vig_prob_under)
        """
        implied_over = self.calculate_implied_probability(odds_over)
        implied_under = self.calculate_implied_probability(odds_under)
        
        total_implied = implied_over + implied_under
        vig = total_implied - 1
        
        no_vig_over = implied_over / total_implied
        no_vig_under = implied_under / total_implied
        
        return no_vig_over, no_vig_under, vig
    
    def calculate_decimal_odds(self, american_odds: int) -> float:
        """Convert American odds to decimal odds."""
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1
    
    def calculate_ev(self, your_prob: float, odds: int) -> float:
        """
        Calculate Expected Value for a bet.
        
        Args:
            your_prob: Your estimated probability of winning
            odds: American odds
            
        Returns:
            Expected Value as decimal (0.05 = 5% edge)
        """
        decimal_odds = self.calculate_decimal_odds(odds)
        return (your_prob * (decimal_odds - 1)) - (1 - your_prob)
    
    def calculate_live_total_projection(self, game_state: Dict) -> Dict:
        """
        Calculate live total projection based on current game state.
        
        Args:
            game_state: Dictionary containing current game information
            
        Returns:
            Dictionary with projection details
        """
        # Extract game state variables
        home_score = game_state.get('home_score', 0)
        away_score = game_state.get('away_score', 0)
        current_total = home_score + away_score
        
        quarter = game_state.get('quarter', 1)
        minutes_remaining = game_state.get('minutes_remaining_reg', 60.0)
        
        # Team pace and efficiency metrics
        home_ppm = game_state.get('home_ppm_estimate', 0.64)  # Points per minute
        away_ppm = game_state.get('away_ppm_estimate', 0.64)
        
        # Calculate average points per minute
        avg_ppm = (home_ppm + away_ppm) / 2
        
        # Base projection: current points + remaining time projection
        base_projection = current_total + (minutes_remaining * avg_ppm)
        
        # Quarter-specific adjustments
        quarter_adjustments = {
            1: 1.05,  # First quarter tends to be slightly higher scoring
            2: 1.02,  # Second quarter normal
            3: 0.98,  # Third quarter slightly lower (halftime adjustments)
            4: 1.08   # Fourth quarter higher (urgency, garbage time)
        }
        
        quarter_adj = quarter_adjustments.get(quarter, 1.0)
        
        # EPA-based adjustments if available
        home_epa = game_state.get('home_off_epa_per_play', 0)
        away_epa = game_state.get('away_off_epa_per_play', 0)
        home_def_epa = game_state.get('home_def_epa_per_play', 0)
        away_def_epa = game_state.get('away_def_epa_per_play', 0)
        
        # Net EPA advantage
        home_net_epa = home_epa - away_def_epa
        away_net_epa = away_epa - home_def_epa
        total_epa_impact = (home_net_epa + away_net_epa) * 2  # Convert to points
        
        # Final projection with adjustments
        final_projection = (base_projection * quarter_adj) + total_epa_impact
        
        # Calculate confidence based on variance
        time_factor = max(0.3, minutes_remaining / 60)  # Less confidence as time decreases
        variance = 13.5 * time_factor  # NFL standard deviation adjusted for time
        
        return {
            'projected_final_total': final_projection,
            'current_total': current_total,
            'projected_additional_points': final_projection - current_total,
            'confidence': time_factor,
            'variance': variance,
            'quarter_adjustment': quarter_adj,
            'epa_impact': total_epa_impact,
            'base_projection': base_projection
        }
    
    def calculate_spread_edge(self, game_data: Dict, spread_line: float, spread_odds: int) -> Dict:
        """
        Calculate spread betting edge using EPA and team ratings.
        
        Args:
            game_data: Game and team statistics
            spread_line: Point spread (negative for home favorite)
            spread_odds: Odds for the spread bet
            
        Returns:
            Dictionary with spread analysis
        """
        # Team ratings and EPA metrics
        home_rating = game_data.get('home_team_rating', 1500)
        away_rating = game_data.get('away_team_rating', 1500)
        
        home_off_epa = game_data.get('home_off_epa_per_play', 0)
        away_off_epa = game_data.get('away_off_epa_per_play', 0)
        home_def_epa = game_data.get('home_def_epa_per_play', 0)
        away_def_epa = game_data.get('away_def_epa_per_play', 0)
        
        # Home field advantage
        home_advantage = game_data.get('home_field_advantage', 3.0)
        
        # Calculate projected margin
        rating_diff = (home_rating - away_rating) / 25  # Convert Elo to points
        epa_diff = (home_off_epa - away_def_epa) - (away_off_epa - home_def_epa)
        epa_points = epa_diff * 70  # Approximate plays per game
        
        projected_margin = rating_diff + epa_points + home_advantage
        
        # Calculate probability of covering spread using normal distribution
        margin_vs_spread = projected_margin - spread_line
        std_dev = 13.5  # NFL standard deviation for point margins
        
        prob_cover = 1 - stats.norm.cdf(0, margin_vs_spread, std_dev)
        
        # Calculate EV
        ev = self.calculate_ev(prob_cover, spread_odds)
        
        return {
            'projected_margin': projected_margin,
            'spread_line': spread_line,
            'margin_vs_spread': margin_vs_spread,
            'prob_cover': prob_cover,
            'ev': ev,
            'ev_percentage': ev * 100,
            'recommendation': self.get_recommendation(ev),
            'confidence': abs(margin_vs_spread) / std_dev
        }
    
    def calculate_moneyline_edge(self, game_data: Dict, home_odds: int, away_odds: int) -> Dict:
        """
        Calculate moneyline betting edge using Elo ratings and EPA.
        
        Args:
            game_data: Game and team statistics
            home_odds: Home team moneyline odds
            away_odds: Away team moneyline odds
            
        Returns:
            Dictionary with moneyline analysis
        """
        # Team ratings
        home_rating = game_data.get('home_team_rating', 1500)
        away_rating = game_data.get('away_team_rating', 1500)
        
        # Calculate win probability using Elo formula
        rating_diff = home_rating - away_rating
        home_win_prob = 1 / (1 + 10**(-rating_diff / 400))
        
        # Adjust for home field advantage (typically 3 points = ~6% win prob boost)
        home_advantage = game_data.get('home_field_advantage', 3.0)
        home_win_prob += (home_advantage / 50)  # Rough conversion
        home_win_prob = max(0.01, min(0.99, home_win_prob))
        
        away_win_prob = 1 - home_win_prob
        
        # Calculate EV for both sides
        home_ev = self.calculate_ev(home_win_prob, home_odds)
        away_ev = self.calculate_ev(away_win_prob, away_odds)
        
        return {
            'home_win_prob': home_win_prob,
            'away_win_prob': away_win_prob,
            'home_ev': home_ev,
            'away_ev': away_ev,
            'home_ev_percentage': home_ev * 100,
            'away_ev_percentage': away_ev * 100,
            'best_bet': 'home' if home_ev > away_ev else 'away',
            'best_ev': max(home_ev, away_ev),
            'recommendation': self.get_recommendation(max(home_ev, away_ev))
        }
    
    def calculate_total_edge_live(self, game_state: Dict, total_line: float, 
                                 over_odds: int, under_odds: int) -> Dict:
        """
        Calculate over/under edge for live betting with enhanced projections.
        
        Args:
            game_state: Current game state and team stats
            total_line: Over/under line
            over_odds: Over odds
            under_odds: Under odds
            
        Returns:
            Dictionary with total betting analysis
        """
        # Get live projection
        projection = self.calculate_live_total_projection(game_state)
        projected_total = projection['projected_final_total']
        variance = projection['variance']
        
        # Calculate probabilities using normal distribution
        prob_over = 1 - stats.norm.cdf(total_line, projected_total, variance)
        prob_under = stats.norm.cdf(total_line, projected_total, variance)
        
        # Calculate EV for both sides
        over_ev = self.calculate_ev(prob_over, over_odds)
        under_ev = self.calculate_ev(prob_under, under_odds)
        
        # Remove vig for comparison
        no_vig_over, no_vig_under, vig = self.calculate_no_vig_probability(over_odds, under_odds)
        
        return {
            'projected_total': projected_total,
            'total_line': total_line,
            'prob_over': prob_over,
            'prob_under': prob_under,
            'over_ev': over_ev,
            'under_ev': under_ev,
            'over_ev_percentage': over_ev * 100,
            'under_ev_percentage': under_ev * 100,
            'best_bet': 'over' if over_ev > under_ev else 'under',
            'best_ev': max(over_ev, under_ev),
            'recommendation': self.get_recommendation(max(over_ev, under_ev)),
            'vig': vig * 100,
            'no_vig_over': no_vig_over,
            'no_vig_under': no_vig_under,
            'projection_details': projection
        }
    
    def get_recommendation(self, ev: float) -> str:
        """
        Get betting recommendation based on EV.
        
        Args:
            ev: Expected value as decimal
            
        Returns:
            Recommendation string
        """
        if ev >= 0.10:
            return "STRONG_BET"
        elif ev >= 0.05:
            return "GOOD_BET"
        elif ev >= 0.03:
            return "CONSIDER"
        elif ev >= 0.01:
            return "SLIGHT_EDGE"
        elif ev >= -0.01:
            return "PASS"
        else:
            return "AVOID"
    
    async def get_ai_analysis(self, game_data: Dict, betting_analysis: Dict) -> str:
        """
        Use ChatGPT to provide intelligent analysis of betting opportunities.
        
        Args:
            game_data: Game information and statistics
            betting_analysis: Calculated betting edges and recommendations
            
        Returns:
            AI-generated analysis string
        """
        try:
            prompt = f"""
            Analyze this NFL/NCAAF betting opportunity:
            
            Game: {game_data.get('away_team', 'Away')} @ {game_data.get('home_team', 'Home')}
            
            Betting Analysis:
            - Best EV: {betting_analysis.get('best_ev', 0):.3f} ({betting_analysis.get('best_ev', 0)*100:.1f}%)
            - Recommendation: {betting_analysis.get('recommendation', 'PASS')}
            - Projected Total: {betting_analysis.get('projected_total', 'N/A')}
            - Line: {betting_analysis.get('total_line', 'N/A')}
            
            Team Stats:
            - Home Rating: {game_data.get('home_team_rating', 'N/A')}
            - Away Rating: {game_data.get('away_team_rating', 'N/A')}
            - Home EPA/Play: {game_data.get('home_off_epa_per_play', 'N/A')}
            - Away EPA/Play: {game_data.get('away_off_epa_per_play', 'N/A')}
            
            Provide a concise analysis focusing on:
            1. Key factors driving the edge
            2. Risk assessment
            3. Confidence level
            4. Any situational factors to consider
            
            Keep response under 200 words and actionable.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert sports betting analyst specializing in NFL and college football. Provide clear, actionable insights based on statistical analysis."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.3
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error getting AI analysis: {str(e)}")
            return "AI analysis unavailable. Rely on statistical calculations for betting decisions."
    
    def comprehensive_game_analysis(self, game_data: Dict, odds_data: Dict) -> Dict:
        """
        Perform comprehensive analysis of all betting markets for a game.
        
        Args:
            game_data: Game and team statistics
            odds_data: Current odds for all markets
            
        Returns:
            Complete analysis dictionary
        """
        results = {
            'game_info': {
                'home_team': game_data.get('home_team'),
                'away_team': game_data.get('away_team'),
                'game_id': game_data.get('game_id')
            },
            'analysis_timestamp': pd.Timestamp.now().isoformat()
        }
        
        # Moneyline analysis
        if 'moneyline' in odds_data:
            ml_data = odds_data['moneyline']
            results['moneyline'] = self.calculate_moneyline_edge(
                game_data, ml_data.get('home'), ml_data.get('away')
            )
        
        # Spread analysis
        if 'spread' in odds_data:
            spread_data = odds_data['spread']
            results['spread'] = self.calculate_spread_edge(
                game_data, spread_data.get('spread'), spread_data.get('home_odds')
            )
        
        # Total analysis (live or pre-game)
        if 'total' in odds_data:
            total_data = odds_data['total']
            if game_data.get('is_live', False):
                results['total'] = self.calculate_total_edge_live(
                    game_data, total_data.get('total'), 
                    total_data.get('over_odds'), total_data.get('under_odds')
                )
            else:
                # Use simpler pre-game total calculation
                results['total'] = self.calculate_pregame_total_edge(
                    game_data, total_data.get('total'),
                    total_data.get('over_odds'), total_data.get('under_odds')
                )
        
        # Find best overall opportunity
        best_ev = -1
        best_market = None
        
        for market, analysis in results.items():
            if isinstance(analysis, dict) and 'best_ev' in analysis:
                if analysis['best_ev'] > best_ev:
                    best_ev = analysis['best_ev']
                    best_market = market
        
        results['summary'] = {
            'best_market': best_market,
            'best_ev': best_ev,
            'best_ev_percentage': best_ev * 100,
            'overall_recommendation': self.get_recommendation(best_ev)
        }
        
        return results
    
    def calculate_pregame_total_edge(self, game_data: Dict, total_line: float, 
                                   over_odds: int, under_odds: int) -> Dict:
        """
        Calculate pre-game total edge using team statistics.
        
        Args:
            game_data: Team statistics and ratings
            total_line: Over/under line
            over_odds: Over odds
            under_odds: Under odds
            
        Returns:
            Dictionary with total analysis
        """
        # Team offensive and defensive ratings
        home_off_rating = game_data.get('home_team_offense_rating', 100)
        away_off_rating = game_data.get('away_team_offense_rating', 100)
        home_def_rating = game_data.get('home_team_defense_rating', 100)
        away_def_rating = game_data.get('away_team_defense_rating', 100)
        
        # Project total points
        # Higher offensive rating = more points, higher defensive rating = fewer points allowed
        home_projected = (home_off_rating / 100) * 24 - (away_def_rating / 100) * 3
        away_projected = (away_off_rating / 100) * 24 - (home_def_rating / 100) * 3
        
        projected_total = home_projected + away_projected
        
        # Add weather and situational adjustments
        weather_impact = game_data.get('weather_impact', 0)
        projected_total += weather_impact
        
        # Calculate probabilities
        variance = 14.0  # Pre-game variance slightly higher
        prob_over = 1 - stats.norm.cdf(total_line, projected_total, variance)
        prob_under = stats.norm.cdf(total_line, projected_total, variance)
        
        # Calculate EV
        over_ev = self.calculate_ev(prob_over, over_odds)
        under_ev = self.calculate_ev(prob_under, under_odds)
        
        return {
            'projected_total': projected_total,
            'total_line': total_line,
            'prob_over': prob_over,
            'prob_under': prob_under,
            'over_ev': over_ev,
            'under_ev': under_ev,
            'over_ev_percentage': over_ev * 100,
            'under_ev_percentage': under_ev * 100,
            'best_bet': 'over' if over_ev > under_ev else 'under',
            'best_ev': max(over_ev, under_ev),
            'recommendation': self.get_recommendation(max(over_ev, under_ev))
        }
