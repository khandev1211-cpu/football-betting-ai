"""
Expected Value Calculator for Football Betting
Calculates Expected Value (EV) for various betting markets and identifies profitable opportunities.
"""

import math
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class EVCalculator:
    """
    Expected Value calculator for football betting markets.
    Handles moneyline, spread, and totals betting calculations.
    """
    
    def __init__(self):
        """Initialize the EV calculator."""
        self.min_ev_threshold = 0.02  # Minimum 2% EV to consider a bet
        self.min_confidence_threshold = 0.6  # Minimum confidence to recommend bet
    
    def american_to_decimal(self, american_odds: int) -> float:
        """
        Convert American odds to decimal odds.
        
        Args:
            american_odds: American odds (e.g., -110, +150)
            
        Returns:
            Decimal odds
        """
        if american_odds > 0:
            return (american_odds / 100) + 1
        else:
            return (100 / abs(american_odds)) + 1
    
    def decimal_to_american(self, decimal_odds: float) -> int:
        """
        Convert decimal odds to American odds.
        
        Args:
            decimal_odds: Decimal odds (e.g., 1.91, 2.50)
            
        Returns:
            American odds
        """
        if decimal_odds >= 2.0:
            return int((decimal_odds - 1) * 100)
        else:
            return int(-100 / (decimal_odds - 1))
    
    def implied_probability(self, american_odds: int) -> float:
        """
        Calculate implied probability from American odds.
        
        Args:
            american_odds: American odds
            
        Returns:
            Implied probability (0-1)
        """
        decimal_odds = self.american_to_decimal(american_odds)
        return 1 / decimal_odds
    
    def calculate_ev(self, true_probability: float, odds: int, bet_amount: float = 100) -> Dict:
        """
        Calculate Expected Value for a bet using the correct formula:
        EV = (P_win × W) - (P_loss × L)
        
        Args:
            true_probability: Our estimated probability of the outcome (0-1)
            odds: American odds offered by the sportsbook
            bet_amount: Amount to bet (default $100)
            
        Returns:
            Dictionary containing EV calculations
        """
        decimal_odds = self.american_to_decimal(odds)
        implied_prob = self.implied_probability(odds)
        
        # Calculate potential profit (W in the formula)
        if odds > 0:
            potential_profit = bet_amount * (odds / 100)
        else:
            potential_profit = bet_amount * (100 / abs(odds))
        
        # Calculate Expected Value using correct formula
        # EV = (P_win × W) - (P_loss × L)
        # Where W = profit if win, L = loss if lose (bet_amount)
        p_win = true_probability
        p_loss = 1 - true_probability
        
        ev = (p_win * potential_profit) - (p_loss * bet_amount)
        ev_percentage = (ev / bet_amount) * 100
        
        # Calculate edge (difference between true and implied probability)
        edge = true_probability - implied_prob
        edge_percentage = edge * 100
        
        # Validate EV percentage is reasonable (should typically be -50% to +20%)
        if ev_percentage > 50:
            logger.warning(f"Unusually high EV calculated: {ev_percentage:.2f}% - check inputs")
        
        return {
            'expected_value': ev,
            'ev_percentage': ev_percentage,
            'edge': edge,
            'edge_percentage': edge_percentage,
            'implied_probability': implied_prob,
            'true_probability': true_probability,
            'decimal_odds': decimal_odds,
            'potential_profit': potential_profit,
            'bet_amount': bet_amount,
            'is_profitable': ev > 0,
            'recommendation': self._get_recommendation(ev_percentage, true_probability)
        }
    
    def _get_recommendation(self, ev_percentage: float, confidence: float) -> str:
        """
        Get betting recommendation based on EV and confidence.
        
        Args:
            ev_percentage: Expected Value percentage
            confidence: Confidence in the prediction (0-1)
            
        Returns:
            Recommendation string
        """
        if ev_percentage < 0:
            return "AVOID"
        elif ev_percentage < self.min_ev_threshold * 100:
            return "PASS"
        elif confidence < self.min_confidence_threshold:
            return "LOW_CONFIDENCE"
        elif ev_percentage >= 10:
            return "STRONG_BET"
        elif ev_percentage >= 5:
            return "GOOD_BET"
        else:
            return "CONSIDER"
    
    def calculate_moneyline_ev(self, predictions: Dict, odds: Dict) -> Dict:
        """
        Calculate EV for moneyline bets.
        
        Args:
            predictions: Prediction results from the model
            odds: Dictionary containing moneyline odds
            
        Returns:
            Dictionary with moneyline EV calculations
        """
        results = {}
        
        # Home team moneyline
        if 'home' in odds:
            home_ev = self.calculate_ev(
                predictions['home_win_probability'],
                odds['home'],
                100
            )
            results['home_moneyline'] = home_ev
        
        # Away team moneyline
        if 'away' in odds:
            away_ev = self.calculate_ev(
                predictions['away_win_probability'],
                odds['away'],
                100
            )
            results['away_moneyline'] = away_ev
        
        return results
    
    def calculate_spread_ev(self, predictions: Dict, spread_data: Dict) -> Dict:
        """
        Calculate EV for spread bets.
        
        Args:
            predictions: Prediction results from the model
            spread_data: Dictionary containing spread and odds
            
        Returns:
            Dictionary with spread EV calculations
        """
        results = {}
        
        predicted_spread = predictions.get('predicted_spread', 0)
        actual_spread = spread_data.get('spread', 0)
        home_odds = spread_data.get('home_odds', -110)
        away_odds = spread_data.get('away_odds', -110)
        
        # Calculate probability of covering spread
        spread_difference = predicted_spread - actual_spread
        
        # Use normal distribution to estimate probability
        # Standard deviation of 3.5 points is typical for NFL
        std_dev = 3.5
        
        # Home team covering spread probability
        home_cover_prob = self._normal_cdf(spread_difference, 0, std_dev)
        away_cover_prob = 1 - home_cover_prob
        
        # Calculate EV for each side
        if home_odds:
            home_spread_ev = self.calculate_ev(home_cover_prob, home_odds, 100)
            results['home_spread'] = home_spread_ev
        
        if away_odds:
            away_spread_ev = self.calculate_ev(away_cover_prob, away_odds, 100)
            results['away_spread'] = away_spread_ev
        
        return results
    
    def calculate_total_ev(self, predictions: Dict, total_data: Dict) -> Dict:
        """
        Calculate EV for over/under total bets.
        
        Args:
            predictions: Prediction results from the model
            total_data: Dictionary containing total and odds
            
        Returns:
            Dictionary with total EV calculations
        """
        results = {}
        
        predicted_total = predictions.get('predicted_total', 45)
        betting_total = total_data.get('total', 45)
        over_odds = total_data.get('over_odds', -110)
        under_odds = total_data.get('under_odds', -110)
        
        # Calculate probability of going over/under
        total_difference = predicted_total - betting_total
        
        # Standard deviation of 6 points is typical for NFL totals
        std_dev = 6.0
        
        # Over probability
        over_prob = 1 - self._normal_cdf(0, total_difference, std_dev)
        under_prob = 1 - over_prob
        
        # Calculate EV for each side
        if over_odds:
            over_ev = self.calculate_ev(over_prob, over_odds, 100)
            results['over'] = over_ev
        
        if under_odds:
            under_ev = self.calculate_ev(under_prob, under_odds, 100)
            results['under'] = under_ev
        
        return results
    
    def _normal_cdf(self, x: float, mean: float = 0, std_dev: float = 1) -> float:
        """
        Calculate cumulative distribution function for normal distribution.
        
        Args:
            x: Value to calculate CDF for
            mean: Mean of the distribution
            std_dev: Standard deviation of the distribution
            
        Returns:
            CDF value
        """
        return 0.5 * (1 + math.erf((x - mean) / (std_dev * math.sqrt(2))))
    
    def calculate_all_markets_ev(self, predictions: Dict, odds_data: Dict) -> Dict:
        """
        Calculate EV for all available betting markets.
        
        Args:
            predictions: Prediction results from the model
            odds_data: Dictionary containing all odds data
            
        Returns:
            Dictionary with EV calculations for all markets
        """
        all_ev = {}
        
        # Moneyline EV
        if 'moneyline' in odds_data:
            moneyline_ev = self.calculate_moneyline_ev(predictions, odds_data['moneyline'])
            all_ev.update(moneyline_ev)
        
        # Spread EV
        if 'spread' in odds_data:
            spread_ev = self.calculate_spread_ev(predictions, odds_data['spread'])
            all_ev.update(spread_ev)
        
        # Total EV
        if 'total' in odds_data:
            total_ev = self.calculate_total_ev(predictions, odds_data['total'])
            all_ev.update(total_ev)
        
        return all_ev
    
    def find_best_bets(self, all_ev: Dict, min_ev: float = None) -> List[Dict]:
        """
        Find the best betting opportunities based on EV.
        
        Args:
            all_ev: Dictionary containing all EV calculations
            min_ev: Minimum EV percentage to consider (default uses class threshold)
            
        Returns:
            List of best betting opportunities sorted by EV
        """
        min_ev = min_ev or (self.min_ev_threshold * 100)
        
        best_bets = []
        
        for market, ev_data in all_ev.items():
            if ev_data['ev_percentage'] >= min_ev and ev_data['recommendation'] not in ['AVOID', 'PASS']:
                bet_info = {
                    'market': market,
                    'ev_percentage': ev_data['ev_percentage'],
                    'expected_value': ev_data['expected_value'],
                    'edge_percentage': ev_data['edge_percentage'],
                    'recommendation': ev_data['recommendation'],
                    'true_probability': ev_data['true_probability'],
                    'implied_probability': ev_data['implied_probability'],
                    'potential_profit': ev_data['potential_profit']
                }
                best_bets.append(bet_info)
        
        # Sort by EV percentage (highest first)
        best_bets.sort(key=lambda x: x['ev_percentage'], reverse=True)
        
        return best_bets
    
    def calculate_kelly_criterion(self, ev_data: Dict, bankroll: float) -> Dict:
        """
        Calculate optimal bet size using Kelly Criterion.
        
        Args:
            ev_data: EV calculation results
            bankroll: Total bankroll amount
            
        Returns:
            Dictionary with Kelly Criterion calculations
        """
        if ev_data['expected_value'] <= 0:
            return {
                'kelly_percentage': 0,
                'recommended_bet': 0,
                'reason': 'Negative EV - do not bet'
            }
        
        # Kelly formula: f = (bp - q) / b
        # where f = fraction of bankroll to bet
        # b = odds received (decimal odds - 1)
        # p = probability of winning
        # q = probability of losing (1 - p)
        
        b = ev_data['decimal_odds'] - 1
        p = ev_data['true_probability']
        q = 1 - p
        
        kelly_fraction = (b * p - q) / b
        
        # Apply fractional Kelly (typically 25% of full Kelly for safety)
        fractional_kelly = kelly_fraction * 0.25
        
        # Cap at 5% of bankroll for risk management
        kelly_percentage = min(fractional_kelly, 0.05) * 100
        recommended_bet = bankroll * (kelly_percentage / 100)
        
        return {
            'kelly_percentage': kelly_percentage,
            'full_kelly_percentage': kelly_fraction * 100,
            'recommended_bet': recommended_bet,
            'reason': 'Fractional Kelly (25% of full Kelly) with 5% max cap'
        }
    
    def generate_betting_summary(self, game_data: Dict, predictions: Dict, 
                                odds_data: Dict, bankroll: float = 1000) -> Dict:
        """
        Generate a comprehensive betting summary for a game.
        
        Args:
            game_data: Game information
            predictions: Model predictions
            odds_data: All odds data
            bankroll: Available bankroll
            
        Returns:
            Comprehensive betting summary
        """
        # Calculate EV for all markets
        all_ev = self.calculate_all_markets_ev(predictions, odds_data)
        
        # Find best bets
        best_bets = self.find_best_bets(all_ev)
        
        # Calculate Kelly Criterion for best bets
        for bet in best_bets:
            market_ev = all_ev[bet['market']]
            kelly_info = self.calculate_kelly_criterion(market_ev, bankroll)
            bet['kelly_info'] = kelly_info
        
        summary = {
            'game_info': {
                'home_team': game_data.get('home_team', 'Unknown'),
                'away_team': game_data.get('away_team', 'Unknown'),
                'game_time': game_data.get('game_time', 'TBD')
            },
            'predictions': predictions,
            'all_ev_calculations': all_ev,
            'best_bets': best_bets,
            'total_opportunities': len(best_bets),
            'highest_ev': max([bet['ev_percentage'] for bet in best_bets]) if best_bets else 0,
            'recommendation_summary': self._generate_recommendation_summary(best_bets)
        }
        
        return summary
    
    def _generate_recommendation_summary(self, best_bets: List[Dict]) -> str:
        """
        Generate a text summary of betting recommendations.
        
        Args:
            best_bets: List of best betting opportunities
            
        Returns:
            Text summary of recommendations
        """
        if not best_bets:
            return "No profitable betting opportunities identified for this game."
        
        strong_bets = [bet for bet in best_bets if bet['recommendation'] == 'STRONG_BET']
        good_bets = [bet for bet in best_bets if bet['recommendation'] == 'GOOD_BET']
        
        summary_parts = []
        
        if strong_bets:
            markets = [bet['market'] for bet in strong_bets]
            summary_parts.append(f"Strong betting opportunities: {', '.join(markets)}")
        
        if good_bets:
            markets = [bet['market'] for bet in good_bets]
            summary_parts.append(f"Good betting opportunities: {', '.join(markets)}")
        
        if best_bets:
            best_bet = best_bets[0]
            summary_parts.append(f"Best bet: {best_bet['market']} with {best_bet['ev_percentage']:.1f}% EV")
        
        return ". ".join(summary_parts) + "."

