"""
Live Betting Engine with Real-Time Projections
Implements live game analysis with EPA-based models and real-time alerts.
"""

import os
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable
import logging
import pandas as pd
import numpy as np
from dataclasses import dataclass
from .advanced_ev_calculator import AdvancedEVCalculator
from .api_fetcher import OddsFetcher

logger = logging.getLogger(__name__)

@dataclass
class LiveGameState:
    """Structure for live game state data."""
    game_id: str
    home_team: str
    away_team: str
    home_score: int
    away_score: int
    quarter: int
    clock: str
    minutes_remaining: float
    is_live: bool
    last_updated: datetime
    
    # Team performance metrics
    home_ppm_estimate: float = 0.64
    away_ppm_estimate: float = 0.64
    home_off_epa_per_play: float = 0.0
    away_off_epa_per_play: float = 0.0
    home_def_epa_per_play: float = 0.0
    away_def_epa_per_play: float = 0.0
    
    # Situational factors
    home_timeouts: int = 3
    away_timeouts: int = 3
    possession: str = "home"
    down: int = 1
    distance: int = 10
    field_position: int = 50

@dataclass
class BettingAlert:
    """Structure for betting opportunity alerts."""
    game_id: str
    market: str
    recommendation: str
    ev_percentage: float
    confidence: float
    message: str
    timestamp: datetime
    odds_data: Dict
    analysis: Dict

class LiveBettingEngine:
    def __init__(self):
        self.ev_calculator = AdvancedEVCalculator()
        self.odds_fetcher = OddsFetcher()
        self.active_games: Dict[str, LiveGameState] = {}
        self.alert_callbacks: List[Callable] = []
        self.min_ev_threshold = 0.03  # 3% minimum EV for alerts
        self.is_monitoring = False
        
    def add_alert_callback(self, callback: Callable[[BettingAlert], None]):
        """Add callback function for betting alerts."""
        self.alert_callbacks.append(callback)
    
    def update_game_state(self, game_data: Dict) -> LiveGameState:
        """
        Update live game state with new data.
        
        Args:
            game_data: Dictionary containing live game information
            
        Returns:
            Updated LiveGameState object
        """
        game_id = game_data.get('game_id')
        
        # Create or update game state
        if game_id in self.active_games:
            game_state = self.active_games[game_id]
            # Update with new data
            game_state.home_score = game_data.get('home_score', game_state.home_score)
            game_state.away_score = game_data.get('away_score', game_state.away_score)
            game_state.quarter = game_data.get('quarter', game_state.quarter)
            game_state.clock = game_data.get('clock', game_state.clock)
            game_state.minutes_remaining = game_data.get('minutes_remaining', game_state.minutes_remaining)
            game_state.last_updated = datetime.now()
        else:
            # Create new game state
            game_state = LiveGameState(
                game_id=game_id,
                home_team=game_data.get('home_team', ''),
                away_team=game_data.get('away_team', ''),
                home_score=game_data.get('home_score', 0),
                away_score=game_data.get('away_score', 0),
                quarter=game_data.get('quarter', 1),
                clock=game_data.get('clock', '15:00'),
                minutes_remaining=game_data.get('minutes_remaining', 60.0),
                is_live=True,
                last_updated=datetime.now()
            )
            
            # Add team performance metrics if available
            for field in ['home_ppm_estimate', 'away_ppm_estimate', 'home_off_epa_per_play',
                         'away_off_epa_per_play', 'home_def_epa_per_play', 'away_def_epa_per_play']:
                if field in game_data:
                    setattr(game_state, field, game_data[field])
        
        self.active_games[game_id] = game_state
        return game_state
    
    def calculate_live_edge(self, game_id: str, odds_data: Dict) -> Optional[Dict]:
        """
        Calculate betting edge for live game.
        
        Args:
            game_id: Game identifier
            odds_data: Current live odds
            
        Returns:
            Dictionary with edge analysis or None if game not found
        """
        if game_id not in self.active_games:
            logger.warning(f"Game {game_id} not found in active games")
            return None
        
        game_state = self.active_games[game_id]
        
        # Convert game state to dictionary for calculations
        game_data = {
            'game_id': game_state.game_id,
            'home_team': game_state.home_team,
            'away_team': game_state.away_team,
            'home_score': game_state.home_score,
            'away_score': game_state.away_score,
            'quarter': game_state.quarter,
            'minutes_remaining_reg': game_state.minutes_remaining,
            'home_ppm_estimate': game_state.home_ppm_estimate,
            'away_ppm_estimate': game_state.away_ppm_estimate,
            'home_off_epa_per_play': game_state.home_off_epa_per_play,
            'away_off_epa_per_play': game_state.away_off_epa_per_play,
            'home_def_epa_per_play': game_state.home_def_epa_per_play,
            'away_def_epa_per_play': game_state.away_def_epa_per_play,
            'is_live': True
        }
        
        # Perform comprehensive analysis
        analysis = self.ev_calculator.comprehensive_game_analysis(game_data, odds_data)
        
        # Add live-specific metrics
        analysis['live_metrics'] = {
            'current_total': game_state.home_score + game_state.away_score,
            'time_remaining_factor': game_state.minutes_remaining / 60,
            'quarter_factor': self.get_quarter_factor(game_state.quarter),
            'pace_factor': (game_state.home_ppm_estimate + game_state.away_ppm_estimate) / 1.28,  # Normalized to average
            'last_updated': game_state.last_updated.isoformat()
        }
        
        return analysis
    
    def get_quarter_factor(self, quarter: int) -> float:
        """Get scoring factor based on quarter."""
        factors = {1: 1.05, 2: 1.02, 3: 0.98, 4: 1.08}
        return factors.get(quarter, 1.0)
    
    def check_betting_opportunities(self, game_id: str) -> List[BettingAlert]:
        """
        Check for profitable betting opportunities in a live game.
        
        Args:
            game_id: Game identifier
            
        Returns:
            List of betting alerts
        """
        alerts = []
        
        try:
            # Get current odds
            live_odds = self.odds_fetcher.get_game_odds(game_id, 'nfl')
            if not live_odds:
                return alerts
            
            # Calculate edges
            analysis = self.calculate_live_edge(game_id, live_odds)
            if not analysis:
                return alerts
            
            game_state = self.active_games[game_id]
            
            # Check each market for opportunities
            for market, market_analysis in analysis.items():
                if not isinstance(market_analysis, dict) or 'best_ev' not in market_analysis:
                    continue
                
                best_ev = market_analysis['best_ev']
                ev_percentage = best_ev * 100
                
                if best_ev >= self.min_ev_threshold:
                    # Create alert
                    confidence = market_analysis.get('confidence', 0.5)
                    recommendation = market_analysis.get('recommendation', 'CONSIDER')
                    
                    message = self.generate_alert_message(
                        game_state, market, market_analysis, ev_percentage
                    )
                    
                    alert = BettingAlert(
                        game_id=game_id,
                        market=market,
                        recommendation=recommendation,
                        ev_percentage=ev_percentage,
                        confidence=confidence,
                        message=message,
                        timestamp=datetime.now(),
                        odds_data=live_odds,
                        analysis=market_analysis
                    )
                    
                    alerts.append(alert)
            
        except Exception as e:
            logger.error(f"Error checking opportunities for game {game_id}: {str(e)}")
        
        return alerts
    
    def generate_alert_message(self, game_state: LiveGameState, market: str, 
                             analysis: Dict, ev_percentage: float) -> str:
        """Generate human-readable alert message."""
        current_score = f"{game_state.away_team} {game_state.away_score} - {game_state.home_team} {game_state.home_score}"
        time_info = f"Q{game_state.quarter} {game_state.clock}"
        
        if market == 'total':
            projected = analysis.get('projected_total', 0)
            line = analysis.get('total_line', 0)
            best_bet = analysis.get('best_bet', 'over')
            
            return (f"🚨 LIVE TOTAL ALERT\n"
                   f"{current_score} ({time_info})\n"
                   f"Projected: {projected:.1f} | Line: {line}\n"
                   f"Bet {best_bet.upper()} - {ev_percentage:.1f}% EV")
        
        elif market == 'spread':
            spread = analysis.get('spread_line', 0)
            projected_margin = analysis.get('projected_margin', 0)
            
            return (f"🚨 LIVE SPREAD ALERT\n"
                   f"{current_score} ({time_info})\n"
                   f"Spread: {spread} | Projected Margin: {projected_margin:.1f}\n"
                   f"{ev_percentage:.1f}% EV")
        
        elif market == 'moneyline':
            best_bet = analysis.get('best_bet', 'home')
            team = game_state.home_team if best_bet == 'home' else game_state.away_team
            
            return (f"🚨 LIVE MONEYLINE ALERT\n"
                   f"{current_score} ({time_info})\n"
                   f"Bet {team} ML - {ev_percentage:.1f}% EV")
        
        return f"🚨 BETTING OPPORTUNITY\n{current_score} ({time_info})\n{ev_percentage:.1f}% EV"
    
    async def monitor_live_games(self, game_ids: List[str], 
                               check_interval: int = 30) -> None:
        """
        Monitor live games for betting opportunities.
        
        Args:
            game_ids: List of game IDs to monitor
            check_interval: Seconds between checks
        """
        self.is_monitoring = True
        logger.info(f"Starting live monitoring for {len(game_ids)} games")
        
        while self.is_monitoring:
            try:
                for game_id in game_ids:
                    # Update game state (would typically come from live data feed)
                    # For now, we'll simulate with odds updates
                    
                    # Check for opportunities
                    alerts = self.check_betting_opportunities(game_id)
                    
                    # Send alerts
                    for alert in alerts:
                        await self.send_alert(alert)
                
                # Wait before next check
                await asyncio.sleep(check_interval)
                
            except Exception as e:
                logger.error(f"Error in live monitoring: {str(e)}")
                await asyncio.sleep(check_interval)
    
    async def send_alert(self, alert: BettingAlert) -> None:
        """Send alert to all registered callbacks."""
        for callback in self.alert_callbacks:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(alert)
                else:
                    callback(alert)
            except Exception as e:
                logger.error(f"Error sending alert: {str(e)}")
    
    def stop_monitoring(self):
        """Stop live game monitoring."""
        self.is_monitoring = False
        logger.info("Live monitoring stopped")
    
    def get_active_games(self) -> Dict[str, Dict]:
        """Get summary of all active games."""
        summary = {}
        for game_id, game_state in self.active_games.items():
            summary[game_id] = {
                'matchup': f"{game_state.away_team} @ {game_state.home_team}",
                'score': f"{game_state.away_score}-{game_state.home_score}",
                'quarter': game_state.quarter,
                'clock': game_state.clock,
                'minutes_remaining': game_state.minutes_remaining,
                'last_updated': game_state.last_updated.isoformat()
            }
        return summary
    
    def simulate_live_game_update(self, game_id: str, score_update: Dict) -> Dict:
        """
        Simulate a live game update for testing purposes.
        
        Args:
            game_id: Game identifier
            score_update: Dictionary with score and time updates
            
        Returns:
            Updated analysis
        """
        if game_id not in self.active_games:
            logger.warning(f"Game {game_id} not found for simulation")
            return {}
        
        # Update game state
        game_state = self.active_games[game_id]
        game_state.home_score = score_update.get('home_score', game_state.home_score)
        game_state.away_score = score_update.get('away_score', game_state.away_score)
        game_state.quarter = score_update.get('quarter', game_state.quarter)
        game_state.minutes_remaining = score_update.get('minutes_remaining', game_state.minutes_remaining)
        game_state.last_updated = datetime.now()
        
        # Get simulated odds (in real implementation, this would come from live odds feed)
        simulated_odds = {
            'total': {
                'total': 47.5,
                'over_odds': -110,
                'under_odds': -110
            },
            'spread': {
                'spread': -3.5,
                'home_odds': -110,
                'away_odds': -110
            },
            'moneyline': {
                'home': -150,
                'away': +130
            }
        }
        
        # Calculate new analysis
        analysis = self.calculate_live_edge(game_id, simulated_odds)
        
        # Check for alerts
        alerts = self.check_betting_opportunities(game_id)
        
        return {
            'analysis': analysis,
            'alerts': [
                {
                    'market': alert.market,
                    'ev_percentage': alert.ev_percentage,
                    'message': alert.message,
                    'recommendation': alert.recommendation
                }
                for alert in alerts
            ],
            'game_state': {
                'score': f"{game_state.away_score}-{game_state.home_score}",
                'quarter': game_state.quarter,
                'minutes_remaining': game_state.minutes_remaining
            }
        }

# Example usage and testing functions
def example_live_betting_usage():
    """Example of how to use the live betting engine."""
    
    # Initialize engine
    engine = LiveBettingEngine()
    
    # Add alert callback
    def print_alert(alert: BettingAlert):
        print(f"ALERT: {alert.message}")
        print(f"EV: {alert.ev_percentage:.1f}%")
        print(f"Confidence: {alert.confidence:.2f}")
        print("-" * 50)
    
    engine.add_alert_callback(print_alert)
    
    # Simulate game setup
    game_data = {
        'game_id': 'NE@MIA-2025-01-15',
        'home_team': 'Miami Dolphins',
        'away_team': 'New England Patriots',
        'home_score': 14,
        'away_score': 10,
        'quarter': 2,
        'clock': '8:30',
        'minutes_remaining': 38.5,
        'home_ppm_estimate': 0.68,
        'away_ppm_estimate': 0.61,
        'home_off_epa_per_play': 0.05,
        'away_off_epa_per_play': -0.02,
        'home_def_epa_per_play': -0.03,
        'away_def_epa_per_play': 0.01
    }
    
    # Update game state
    game_state = engine.update_game_state(game_data)
    print(f"Game added: {game_state.away_team} @ {game_state.home_team}")
    
    # Simulate score update
    score_update = {
        'home_score': 21,
        'away_score': 10,
        'quarter': 2,
        'minutes_remaining': 35.0
    }
    
    result = engine.simulate_live_game_update('NE@MIA-2025-01-15', score_update)
    print(f"Simulation result: {len(result.get('alerts', []))} alerts generated")
    
    return engine

if __name__ == "__main__":
    # Run example
    engine = example_live_betting_usage()
