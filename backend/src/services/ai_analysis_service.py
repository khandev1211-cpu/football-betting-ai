"""
AI-Powered Betting Analysis Service using OpenAI
Implements intelligent betting recommendations and edge analysis
"""

import openai
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
import os
from .probability_engine import ProbabilityEngine, LiveBettingAnalyzer

logger = logging.getLogger(__name__)

class AIAnalysisService:
    """AI-powered betting analysis using OpenAI GPT"""
    
    def __init__(self, api_key: str):
        self.client = openai.OpenAI(api_key=api_key)
        self.prob_engine = ProbabilityEngine()
        self.betting_analyzer = LiveBettingAnalyzer(self.prob_engine)
        
    def analyze_betting_edge(self, game_data: Dict, odds_data: Dict, context: str = "") -> Dict:
        """
        Comprehensive AI analysis of betting opportunities
        
        Args:
            game_data: Live game state and statistics
            odds_data: Current odds from multiple sportsbooks
            context: Additional context for analysis
        """
        
        # Get quantitative analysis first
        quant_analysis = self.betting_analyzer.analyze_live_game(game_data, odds_data)
        
        # Prepare data for AI analysis
        ai_prompt = self._create_analysis_prompt(game_data, odds_data, quant_analysis, context)
        
        try:
            # Get AI insights
            ai_response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {
                        "role": "system",
                        "content": self._get_system_prompt()
                    },
                    {
                        "role": "user",
                        "content": ai_prompt
                    }
                ],
                temperature=0.3,
                max_tokens=1500
            )
            
            ai_insights = ai_response.choices[0].message.content
            
            # Combine quantitative and AI analysis
            combined_analysis = {
                "timestamp": datetime.now().isoformat(),
                "game_info": {
                    "game_id": game_data.get("game_id"),
                    "matchup": f"{game_data.get('away_team')} @ {game_data.get('home_team')}",
                    "current_score": f"{game_data.get('away_score')}-{game_data.get('home_score')}",
                    "quarter": game_data.get("quarter"),
                    "time_remaining": game_data.get("minutes_remaining")
                },
                "quantitative_analysis": quant_analysis,
                "ai_insights": ai_insights,
                "recommendations": self._extract_recommendations(ai_insights, quant_analysis),
                "risk_assessment": self._assess_risk(quant_analysis),
                "kelly_sizing": self._calculate_kelly_sizing(quant_analysis)
            }
            
            return combined_analysis
            
        except Exception as e:
            logger.error(f"AI analysis failed: {str(e)}")
            return {
                "error": f"AI analysis failed: {str(e)}",
                "quantitative_analysis": quant_analysis,
                "timestamp": datetime.now().isoformat()
            }
    
    async def analyze_game(self, game_data: Dict) -> Dict:
        """Analyze a single game and provide AI betting insights with quota management"""
        try:
            prompt = f"""
            Analyze this football game for betting insights:
            
            Home Team: {game_data.get('home_team', 'Unknown')}
            Away Team: {game_data.get('away_team', 'Unknown')}
            Home Rating: {game_data.get('home_team_rating', 1500)}
            Away Rating: {game_data.get('away_team_rating', 1500)}
            
            Provide brief analysis focusing on:
            1. Confidence level (high/medium/low)
            2. Home team advantage/disadvantage
            3. Key factors affecting the outcome
            
            Keep response under 100 words.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a professional sports betting analyst."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150,
                temperature=0.7
            )
            
            content = response.choices[0].message.content.lower()
            
            # Parse confidence adjustment
            confidence_adjustment = 1.0
            if "confidence" in content:
                if "high" in content or "strong" in content:
                    confidence_adjustment = 1.1
                elif "low" in content or "weak" in content:
                    confidence_adjustment = 0.9
            
            # Parse home team bias
            home_team_bias = 0.0
            if "home" in content:
                if "advantage" in content or "favor" in content:
                    home_team_bias = 0.05
                elif "disadvantage" in content:
                    home_team_bias = -0.05
            
            return {
                'confidence_adjustment': confidence_adjustment,
                'home_team_bias': home_team_bias,
                'analysis': response.choices[0].message.content,
                'reasoning': f"AI confidence: {confidence_adjustment}, Home bias: {home_team_bias}"
            }
            
        except Exception as e:
            error_msg = str(e)
            if "429" in error_msg or "quota" in error_msg.lower() or "insufficient_quota" in error_msg:
                # Silently handle quota exceeded - only log once per session
                if not hasattr(self, '_quota_logged'):
                    logger.warning("OpenAI API quota exceeded. Using fallback analysis.")
                    self._quota_logged = True
                # Return statistical fallback analysis
                return self._get_fallback_analysis(game_data)
            else:
                logger.error(f"AI game analysis failed: {error_msg}")
                return {
                    'confidence_adjustment': 1.0,
                    'home_team_bias': 0.0,
                    'analysis': 'AI analysis unavailable',
                    'reasoning': f'Error: {error_msg}'
                }
    
    def _get_fallback_analysis(self, game_data: Dict) -> Dict:
        """Provide statistical fallback analysis when AI is unavailable"""
        home_rating = game_data.get('home_team_rating', 1500)
        away_rating = game_data.get('away_team_rating', 1500)
        
        # Calculate confidence based on rating difference
        rating_diff = abs(home_rating - away_rating)
        if rating_diff > 200:
            confidence_adjustment = 1.1  # High confidence for large rating gaps
        elif rating_diff < 50:
            confidence_adjustment = 0.9  # Low confidence for close matchups
        else:
            confidence_adjustment = 1.0  # Medium confidence
        
        # Standard home field advantage
        home_team_bias = 0.03  # 3% home field advantage
        
        return {
            'confidence_adjustment': confidence_adjustment,
            'home_team_bias': home_team_bias,
            'analysis': f'Statistical analysis: Rating difference of {rating_diff} points suggests {"high" if rating_diff > 200 else "medium" if rating_diff > 50 else "low"} confidence prediction.',
            'reasoning': f'Fallback analysis - Confidence: {confidence_adjustment}, Home bias: {home_team_bias}'
        }

    def get_live_betting_insights(self, live_games: List[Dict]) -> Dict:
        """Get AI insights for multiple live games"""
        insights = {
            "timestamp": datetime.now().isoformat(),
            "total_games": len(live_games),
            "game_insights": [],
            "market_overview": "",
            "top_opportunities": []
        }
        
        all_opportunities = []
        
        for game in live_games:
            if not game.get("odds_data"):
                continue
                
            game_analysis = self.analyze_betting_edge(
                game.get("game_data", {}),
                game.get("odds_data", {}),
                "Live betting analysis"
            )
            
            insights["game_insights"].append({
                "game_id": game.get("game_id"),
                "analysis": game_analysis
            })
            
            # Collect all opportunities
            if "quantitative_analysis" in game_analysis:
                opportunities = game_analysis["quantitative_analysis"].get("best_bets", [])
                all_opportunities.extend(opportunities)
        
        # Rank top opportunities across all games
        insights["top_opportunities"] = sorted(
            all_opportunities,
            key=lambda x: x.get("expected_value", 0) * x.get("confidence", 0),
            reverse=True
        )[:5]
        
        # Generate market overview
        insights["market_overview"] = self._generate_market_overview(insights["game_insights"])
        
        return insights
    
    def _get_system_prompt(self) -> str:
        """System prompt for AI betting analysis"""
        return """You are an expert sports betting analyst specializing in NFL and college football. 
        Your role is to provide intelligent analysis of betting opportunities using advanced statistical models, 
        EPA (Expected Points Added) metrics, and real-time game data.

        Key principles:
        1. Focus on Expected Value (EV) - only recommend bets with positive EV > 3%
        2. Consider game context: quarter, score differential, weather, injuries
        3. Use EPA/play, pace metrics, and red zone efficiency in analysis
        4. Account for vig and find the best lines across multiple sportsbooks
        5. Provide clear reasoning for each recommendation
        6. Always emphasize responsible gambling and bankroll management

        Analysis framework:
        - Calculate true probabilities using EPA and advanced metrics
        - Compare to implied probabilities from odds
        - Identify edges in totals, spreads, and moneylines
        - Consider live game dynamics and momentum shifts
        - Provide Kelly Criterion bet sizing recommendations

        Output format:
        - Clear recommendation (STRONG BET, GOOD BET, CONSIDER, PASS)
        - Expected value percentage
        - Key factors supporting the bet
        - Risk assessment
        - Suggested bet size as % of bankroll"""
    
    def _create_analysis_prompt(self, game_data: Dict, odds_data: Dict, 
                              quant_analysis: Dict, context: str) -> str:
        """Create detailed prompt for AI analysis"""
        
        prompt = f"""
        Analyze this live betting opportunity:

        GAME SITUATION:
        {game_data.get('away_team')} @ {game_data.get('home_team')}
        Score: {game_data.get('away_score')}-{game_data.get('home_score')}
        Quarter: {game_data.get('quarter')} | Time Remaining: {game_data.get('minutes_remaining')} minutes

        TEAM STATISTICS:
        Home Team ({game_data.get('home_team')}):
        - Offensive EPA/play: {game_data.get('home_team_stats', {}).get('off_epa_per_play', 'N/A')}
        - Defensive EPA/play allowed: {game_data.get('home_team_stats', {}).get('def_epa_per_play_allowed', 'N/A')}
        - Red Zone TD Rate: {game_data.get('home_team_stats', {}).get('red_zone_td_rate', 'N/A')}
        - Pace (sec/play): {game_data.get('home_team_stats', {}).get('pace_seconds_per_play', 'N/A')}

        Away Team ({game_data.get('away_team')}):
        - Offensive EPA/play: {game_data.get('away_team_stats', {}).get('off_epa_per_play', 'N/A')}
        - Defensive EPA/play allowed: {game_data.get('away_team_stats', {}).get('def_epa_per_play_allowed', 'N/A')}
        - Red Zone TD Rate: {game_data.get('away_team_stats', {}).get('red_zone_td_rate', 'N/A')}
        - Pace (sec/play): {game_data.get('away_team_stats', {}).get('pace_seconds_per_play', 'N/A')}

        QUANTITATIVE ANALYSIS:
        {json.dumps(quant_analysis.get('projections', {}), indent=2)}

        BETTING OPPORTUNITIES FOUND:
        {json.dumps(quant_analysis.get('best_bets', []), indent=2)}

        CURRENT ODDS:
        {json.dumps(odds_data, indent=2)}

        CONTEXT: {context}

        Please provide:
        1. Analysis of the top 3 betting opportunities
        2. Key factors influencing your recommendations
        3. Risk assessment for each bet
        4. Overall market assessment
        5. Any situational factors to consider (weather, injuries, motivation)
        """
        
        return prompt
    
    def _extract_recommendations(self, ai_insights: str, quant_analysis: Dict) -> List[Dict]:
        """Extract structured recommendations from AI insights"""
        recommendations = []
        
        # Get top opportunities from quantitative analysis
        best_bets = quant_analysis.get("best_bets", [])
        
        for i, bet in enumerate(best_bets[:3]):  # Top 3 bets
            recommendation = {
                "rank": i + 1,
                "market": bet.get("market"),
                "bookmaker": bet.get("bookmaker"),
                "odds": bet.get("odds"),
                "expected_value": bet.get("expected_value"),
                "confidence": bet.get("confidence"),
                "recommendation": bet.get("recommendation"),
                "ai_reasoning": f"Based on quantitative analysis showing {bet.get('edge_percentage', 0):.1f}% edge"
            }
            recommendations.append(recommendation)
        
        return recommendations
    
    def _assess_risk(self, quant_analysis: Dict) -> Dict:
        """Assess risk levels for betting opportunities"""
        best_bets = quant_analysis.get("best_bets", [])
        
        if not best_bets:
            return {"overall_risk": "HIGH", "reason": "No profitable opportunities identified"}
        
        avg_confidence = sum(bet.get("confidence", 0) for bet in best_bets) / len(best_bets)
        avg_ev = sum(bet.get("expected_value", 0) for bet in best_bets) / len(best_bets)
        
        if avg_confidence > 0.8 and avg_ev > 0.1:
            risk_level = "LOW"
        elif avg_confidence > 0.7 and avg_ev > 0.05:
            risk_level = "MEDIUM"
        else:
            risk_level = "HIGH"
        
        return {
            "overall_risk": risk_level,
            "average_confidence": avg_confidence,
            "average_ev": avg_ev,
            "total_opportunities": len(best_bets)
        }
    
    def _calculate_kelly_sizing(self, quant_analysis: Dict) -> Dict:
        """Calculate Kelly Criterion bet sizing"""
        kelly_recommendations = []
        
        for bet in quant_analysis.get("best_bets", []):
            prob = bet.get("your_probability", 0)
            odds = bet.get("odds", 0)
            
            if odds and prob:
                # Convert to decimal odds
                if odds > 0:
                    decimal_odds = (odds / 100) + 1
                else:
                    decimal_odds = (100 / abs(odds)) + 1
                
                # Kelly formula: f = (bp - q) / b
                # where b = decimal_odds - 1, p = probability, q = 1 - p
                b = decimal_odds - 1
                p = prob
                q = 1 - p
                
                kelly_fraction = (b * p - q) / b
                
                # Apply fractional Kelly (25% of full Kelly for safety)
                safe_kelly = max(0, min(0.05, kelly_fraction * 0.25))  # Cap at 5% of bankroll
                
                kelly_recommendations.append({
                    "market": bet.get("market"),
                    "full_kelly": kelly_fraction,
                    "recommended_fraction": safe_kelly,
                    "recommended_percentage": safe_kelly * 100
                })
        
        return {
            "recommendations": kelly_recommendations,
            "note": "Recommendations use 25% of full Kelly for conservative sizing"
        }
    
    def _generate_market_overview(self, game_insights: List[Dict]) -> str:
        """Generate AI overview of current betting market"""
        try:
            # Prepare summary data
            total_games = len(game_insights)
            total_opportunities = sum(
                len(game.get("analysis", {}).get("quantitative_analysis", {}).get("best_bets", []))
                for game in game_insights
            )
            
            summary_prompt = f"""
            Provide a brief market overview for {total_games} live NFL/college football games 
            with {total_opportunities} total betting opportunities identified.
            
            Focus on:
            1. Overall market conditions
            2. Best betting markets (totals vs spreads vs moneylines)
            3. Key trends observed
            4. Risk factors to watch
            
            Keep response to 2-3 sentences maximum.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a concise sports betting market analyst."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.3,
                max_tokens=200
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Market overview generation failed: {str(e)}")
            return f"Market analysis for {total_games} live games with {total_opportunities} opportunities identified."
