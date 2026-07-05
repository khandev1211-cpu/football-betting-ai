import os
import joblib
import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional
from .ai_analysis_service import AIAnalysisService
from .probability_engine import ProbabilityEngine

logger = logging.getLogger(__name__)

class EnhancedFootballPredictor:
    def __init__(self):
        self.models = {}
        # Initialize AI service with API key from environment
        api_key = os.getenv('OPENAI_API_KEY')
        self.ai_service = AIAnalysisService(api_key) if api_key else None
        self.probability_engine = ProbabilityEngine()
        self.load_all_models()

    def load_all_models(self):
        """Load all available ML models"""
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
        models_dir = os.path.join(backend_dir, 'models')
        
        model_files = {
            'nfl_lgbm': 'nfl_lgbm_model.joblib',
            'football_hist_gb': 'football_hist_gb_model.joblib',
            'predictor': 'predictor.joblib'
        }
        
        for model_name, filename in model_files.items():
            model_path = os.path.join(models_dir, filename)
            try:
                if os.path.exists(model_path):
                    self.models[model_name] = joblib.load(model_path)
                    logger.info(f"Loaded {model_name} model from {model_path}")
                else:
                    logger.warning(f"Model file not found: {model_path}")
            except Exception as e:
                logger.error(f"Error loading {model_name} model: {str(e)}")

    def preprocess_features_for_model(self, game_data: Dict, model_name: str) -> pd.DataFrame:
        """Preprocess features specific to each model's requirements"""
        if model_name == 'nfl_lgbm' or model_name == 'predictor':
            return self._preprocess_nfl_features(game_data)
        elif model_name == 'football_hist_gb':
            return self._preprocess_football_hist_features(game_data)
        else:
            # Fallback to NFL features
            return self._preprocess_nfl_features(game_data)
    
    def _preprocess_nfl_features(self, game_data: Dict) -> pd.DataFrame:
        """Preprocess features for NFL LightGBM and predictor models"""
        # Expected features: ['team_strength_diff', 'over_under_line', 'weather_temperature', 
        # 'weather_wind_mph', 'weather_humidity', 'is_playoff', 'home_avg_pts_scored_L5', 
        # 'home_avg_pts_allowed_L5', 'home_win_pct_L5', 'away_avg_pts_scored_L5', 
        # 'away_avg_pts_allowed_L5', 'away_win_pct_L5', 'home_elo_pre', 'away_elo_pre', 'over_under_diff']
        
        home_rating = game_data.get('home_team_rating', 1500)
        away_rating = game_data.get('away_team_rating', 1500)
        total_line = game_data.get('total', 45.0)
        
        features = {
            'team_strength_diff': home_rating - away_rating,
            'over_under_line': total_line,
            'weather_temperature': game_data.get('weather_temperature', 70.0),
            'weather_wind_mph': game_data.get('weather_wind_mph', 5.0),
            'weather_humidity': game_data.get('weather_humidity', 50.0),
            'is_playoff': int(game_data.get('is_playoff', False)),
            'home_avg_pts_scored_L5': game_data.get('home_avg_pts_scored_L5', 24.0),
            'home_avg_pts_allowed_L5': game_data.get('home_avg_pts_allowed_L5', 21.0),
            'home_win_pct_L5': game_data.get('home_win_pct_L5', 0.6),
            'away_avg_pts_scored_L5': game_data.get('away_avg_pts_scored_L5', 22.0),
            'away_avg_pts_allowed_L5': game_data.get('away_avg_pts_allowed_L5', 23.0),
            'away_win_pct_L5': game_data.get('away_win_pct_L5', 0.4),
            'home_elo_pre': home_rating,
            'away_elo_pre': away_rating,
            'over_under_diff': total_line - 45.0  # Difference from league average
        }
        return pd.DataFrame([features])
    
    def _preprocess_football_hist_features(self, game_data: Dict) -> pd.DataFrame:
        """Preprocess features for football history gradient boosting model"""
        # Expected features: ['HomeElo', 'AwayElo', 'Form3Home', 'Form5Home', 'Form3Away', 'Form5Away',
        # 'OddHome', 'OddDraw', 'OddAway', 'HomeTeam_Goals_Scored_Rolling_5', 
        # 'AwayTeam_Goals_Scored_Rolling_5', 'HomeTeam_Goals_Conceded_Rolling_5',
        # 'AwayTeam_Goals_Conceded_Rolling_5', 'ImpliedProbHome', 'ImpliedProbDraw', 
        # 'ImpliedProbAway', 'OddsRatioHomeAway', 'OddsSpreadHomeAway']
        
        home_rating = game_data.get('home_team_rating', 1500)
        away_rating = game_data.get('away_team_rating', 1500)
        home_ml_odds = game_data.get('home_ml_odds', -110)
        away_ml_odds = game_data.get('away_ml_odds', -110)
        
        # Convert American odds to decimal for calculations
        home_decimal = self._american_to_decimal(home_ml_odds)
        away_decimal = self._american_to_decimal(away_ml_odds)
        draw_decimal = 15.0  # Assume draw odds for soccer-style model
        
        # Calculate implied probabilities
        total_implied = (1/home_decimal) + (1/away_decimal) + (1/draw_decimal)
        implied_home = (1/home_decimal) / total_implied
        implied_away = (1/away_decimal) / total_implied
        implied_draw = (1/draw_decimal) / total_implied
        
        features = {
            'HomeElo': home_rating,
            'AwayElo': away_rating,
            'Form3Home': game_data.get('home_recent_form', 0.6),
            'Form5Home': game_data.get('home_recent_form', 0.6),
            'Form3Away': game_data.get('away_recent_form', 0.4),
            'Form5Away': game_data.get('away_recent_form', 0.4),
            'OddHome': home_decimal,
            'OddDraw': draw_decimal,
            'OddAway': away_decimal,
            'HomeTeam_Goals_Scored_Rolling_5': game_data.get('home_avg_pts_scored_L5', 24.0) / 7,  # Convert to goals
            'AwayTeam_Goals_Scored_Rolling_5': game_data.get('away_avg_pts_scored_L5', 22.0) / 7,
            'HomeTeam_Goals_Conceded_Rolling_5': game_data.get('home_avg_pts_allowed_L5', 21.0) / 7,
            'AwayTeam_Goals_Conceded_Rolling_5': game_data.get('away_avg_pts_allowed_L5', 23.0) / 7,
            'ImpliedProbHome': implied_home,
            'ImpliedProbDraw': implied_draw,
            'ImpliedProbAway': implied_away,
            'OddsRatioHomeAway': home_decimal / away_decimal,
            'OddsSpreadHomeAway': abs(home_ml_odds - away_ml_odds) / 100
        }
        return pd.DataFrame([features])
    
    def _american_to_decimal(self, american_odds: int) -> float:
        """Convert American odds to decimal odds"""
        if american_odds < 0:
            return (100 / abs(american_odds)) + 1
        else:
            return (american_odds / 100) + 1

    def get_ml_predictions(self, game_data: Dict) -> Dict:
        """Get predictions from all available ML models"""
        predictions = {}
        
        for model_name, model in self.models.items():
            try:
                # Get model-specific features
                features = self.preprocess_features_for_model(game_data, model_name)
                
                if hasattr(model, 'predict_proba'):
                    proba = model.predict_proba(features)[0]
                    home_win_proba = float(proba[1]) if len(proba) > 1 else float(proba[0])
                else:
                    pred = model.predict(features)[0]
                    home_win_proba = 0.7 if int(pred) == 1 else 0.3
                
                predictions[model_name] = {
                    'home_win_probability': home_win_proba,
                    'away_win_probability': 1 - home_win_proba,
                    'confidence': abs(home_win_proba - 0.5) * 2
                }
                logger.info(f"Successfully got prediction from {model_name} model")
            except Exception as e:
                logger.error(f"Error with {model_name} model: {str(e)}")
                continue
        
        return predictions

    def ensemble_predictions(self, ml_predictions: Dict) -> Dict:
        """Combine multiple ML model predictions using weighted ensemble"""
        if not ml_predictions:
            return self.get_fallback_prediction()
        
        # Model weights (can be tuned based on historical performance)
        weights = {
            'nfl_lgbm': 0.4,
            'football_hist_gb': 0.35,
            'predictor': 0.25
        }
        
        total_weight = 0
        weighted_home_prob = 0
        weighted_confidence = 0
        
        for model_name, pred in ml_predictions.items():
            weight = weights.get(model_name, 0.2)
            total_weight += weight
            weighted_home_prob += pred['home_win_probability'] * weight
            weighted_confidence += pred['confidence'] * weight
        
        if total_weight > 0:
            weighted_home_prob /= total_weight
            weighted_confidence /= total_weight
        else:
            return self.get_fallback_prediction()
        
        return {
            'home_win_probability': weighted_home_prob,
            'away_win_probability': 1 - weighted_home_prob,
            'confidence': weighted_confidence,
            'prediction_source': 'ml_ensemble'
        }

    def get_fallback_prediction(self) -> Dict:
        """
        Get fallback prediction when models fail.
        
        Returns:
            Dictionary with basic prediction data
        """
        return {
            'home_win_probability': 0.5,
            'away_win_probability': 0.5,
            'confidence_score': 0.6,  # Set to reasonable default instead of 0.5
            'model_used': 'fallback_heuristic',
            'predicted_spread': 0.0,
            'predicted_total': 45.0,
            'prediction_details': {
                'home_team_rating': 1500,
                'away_team_rating': 1500,
                'home_field_advantage': 0.03,
                'prediction_source': 'fallback'
            }
        }

    async def predict_game_comprehensive(self, game_data: Dict, historical_data: Optional[List[Dict]] = None) -> Dict:
        """Comprehensive prediction combining ML models, probability engine, and AI analysis with dataset enhancement"""
        try:
            # Get ML model predictions
            ml_predictions = self.get_ml_predictions(game_data)
            ensemble_pred = self.ensemble_predictions(ml_predictions)
            
            # Get probability engine analysis with AI enhancement
            prob_analysis = self.probability_engine.calculate_game_probabilities(game_data)
            
            # Get dataset-enhanced predictions if historical data is available
            dataset_analysis = None
            if historical_data and self.probability_engine.ai_client:
                from .probability_engine import LiveBettingAnalyzer
                analyzer = LiveBettingAnalyzer(self.probability_engine)
                dataset_analysis = analyzer.get_dataset_enhanced_predictions(game_data, historical_data)
            
            # Get AI analysis if service is available
            if self.ai_service:
                ai_analysis = await self.ai_service.analyze_game(game_data)
            else:
                ai_analysis = {'confidence': 0.5, 'confidence_adjustment': 1.0, 'home_team_bias': 0.0}
            
            # Combine all analyses including dataset insights
            final_prediction = self.combine_all_analyses_enhanced(
                ensemble_pred, prob_analysis, ai_analysis, dataset_analysis, game_data
            )
            
            return final_prediction
            
        except Exception as e:
            logger.error(f"Error in comprehensive prediction: {str(e)}")
            return self.get_fallback_prediction()

    def combine_all_analyses_enhanced(self, ml_pred: Dict, prob_analysis: Dict, 
                                    ai_analysis: Dict, dataset_analysis: Optional[Dict], 
                                    game_data: Dict) -> Dict:
        """Enhanced analysis combination including dataset insights"""
        
        # Weight the different prediction sources
        ml_weight = 0.3
        prob_weight = 0.25
        ai_weight = 0.2
        dataset_weight = 0.25 if dataset_analysis else 0.0
        
        # Adjust weights if dataset analysis is not available
        if not dataset_analysis:
            ml_weight = 0.4
            prob_weight = 0.35
            ai_weight = 0.25
        
        # Extract probabilities from each source
        ml_home_prob = ml_pred.get('home_win_probability', 0.5)
        prob_home_prob = prob_analysis.get('home_win_probability', 0.5)
        
        # AI analysis adjustments
        ai_confidence_adj = ai_analysis.get('confidence_adjustment', 1.0)
        ai_home_bias = ai_analysis.get('home_team_bias', 0.0)
        
        # Dataset analysis adjustments
        dataset_home_adj = 0.0
        if dataset_analysis and 'probability_adjustments' in dataset_analysis:
            dataset_home_adj = dataset_analysis['probability_adjustments'].get('home_win_adjustment', 0.0)
        
        # Combine probabilities
        combined_home_prob = (
            ml_home_prob * ml_weight +
            prob_home_prob * prob_weight +
            (ml_home_prob + ai_home_bias) * ai_weight +
            (prob_home_prob + dataset_home_adj) * dataset_weight
        )
        
        # Ensure probability bounds
        combined_home_prob = max(0.01, min(0.99, combined_home_prob))
        
        # Calculate confidence
        base_confidence = (
            ml_pred.get('confidence', 0.5) * ml_weight +
            prob_analysis.get('confidence', 0.5) * prob_weight +
            ai_analysis.get('confidence', 0.5) * ai_weight
        )
        
        if dataset_analysis:
            dataset_confidence = dataset_analysis.get('confidence_level', 0.5)
            base_confidence += dataset_confidence * dataset_weight
        
        final_confidence = base_confidence * ai_confidence_adj
        final_confidence = max(0.1, min(1.0, final_confidence))
        
        # Determine predicted winner
        predicted_winner = (
            game_data.get('home_team', 'Home') 
            if combined_home_prob > 0.5 
            else game_data.get('away_team', 'Away')
        )
        
        result = {
            'home_win_probability': combined_home_prob,
            'away_win_probability': 1 - combined_home_prob,
            'draw_probability': 0.0,
            'predicted_winner': predicted_winner,
            'confidence': final_confidence,
            'prediction_source': 'enhanced_comprehensive_analysis',
            'ml_prediction': ml_pred,
            'probability_analysis': prob_analysis,
            'ai_analysis': ai_analysis,
            'dataset_analysis': dataset_analysis,
            'model_breakdown': {
                'ml_models_used': list(self.models.keys()),
                'ml_weight': ml_weight,
                'probability_weight': prob_weight,
                'ai_weight': ai_weight,
                'dataset_weight': dataset_weight
            }
        }
        
        return result

    def combine_all_analyses(self, ml_pred: Dict, prob_analysis: Dict, 
                           ai_analysis: Dict, game_data: Dict) -> Dict:
        """Combine ML, probability engine, and AI analyses into final prediction"""
        try:
            # Weight the different prediction sources
            ml_weight = 0.4
            prob_weight = 0.35
            ai_weight = 0.25
            
            # Extract probabilities from each source
            ml_home_prob = ml_pred.get('home_win_probability', 0.5)
            prob_home_prob = prob_analysis.get('home_win_probability', 0.5)
            ai_home_prob = ai_analysis.get('home_win_probability', 0.5)
            
            # Combine probabilities with weights
            final_home_prob = (ml_weight * ml_home_prob + 
                             prob_weight * prob_home_prob + 
                             ai_weight * ai_home_prob)
            
            # Calculate confidence
            ml_confidence = ml_pred.get('confidence', 0.6)
            prob_confidence = prob_analysis.get('confidence', 0.6)
            ai_confidence = ai_analysis.get('confidence', 0.6)
            
            final_confidence = (ml_weight * ml_confidence + 
                              prob_weight * prob_confidence + 
                              ai_weight * ai_confidence)
            
            return {
                'home_win_probability': final_home_prob,
                'away_win_probability': 1 - final_home_prob,
                'confidence_score': final_confidence,
                'model_used': 'combined_analysis'
            }
        except Exception as e:
            logger.error(f"Error combining analyses: {str(e)}")
            return self.get_fallback_prediction()

    def predict_game(self, game_data: Dict) -> Dict:
        """Synchronous game prediction method for API routes"""
        try:
            # Get ML model predictions
            ml_predictions = self.get_ml_predictions(game_data)
            ensemble_pred = self.ensemble_predictions(ml_predictions)
            
            # Get probability engine analysis
            prob_analysis = self.probability_engine.calculate_game_probabilities(game_data)
            
            # Use basic AI analysis without async
            ai_analysis = {'confidence': 0.5, 'confidence_adjustment': 1.0, 'home_team_bias': 0.0}
            
            # Combine all analyses
            final_prediction = self.combine_all_analyses(
                ensemble_pred, prob_analysis, ai_analysis, game_data
            )
            
            # Add additional prediction fields expected by EV calculator
            final_prediction['predicted_spread'] = self._calculate_predicted_spread(final_prediction, game_data)
            final_prediction['predicted_total'] = self._calculate_predicted_total(final_prediction, game_data)
            
            return final_prediction
            
        except Exception as e:
            logger.error(f"Error in game prediction: {str(e)}")
            return self.get_fallback_prediction()
    
    def _calculate_predicted_spread(self, prediction: Dict, game_data: Dict) -> float:
        """Calculate predicted point spread based on win probabilities"""
        home_prob = prediction.get('home_win_probability', 0.5)
        # Convert probability to spread (rough approximation)
        if home_prob > 0.5:
            spread = -((home_prob - 0.5) * 20)  # Negative for home favorite
        else:
            spread = ((0.5 - home_prob) * 20)   # Positive for home underdog
        return round(spread, 1)
    
    def _calculate_predicted_total(self, prediction: Dict, game_data: Dict) -> float:
        """Calculate predicted total points for the game"""
        # Base total around league average
        base_total = 45.0
        
        # Adjust based on team ratings and pace
        home_rating = game_data.get('home_team_rating', 1500)
        away_rating = game_data.get('away_team_rating', 1500)
        
        # Higher rated teams tend to score more
        rating_adjustment = ((home_rating + away_rating) - 3000) / 100
        
        # Pace adjustment
        home_pace = game_data.get('home_pace', 65.0)
        away_pace = game_data.get('away_pace', 65.0)
        avg_pace = (home_pace + away_pace) / 2
        pace_adjustment = (avg_pace - 65.0) / 5.0
        
        predicted_total = base_total + rating_adjustment + pace_adjustment
        return round(max(35.0, min(65.0, predicted_total)), 1)

    def get_model_status(self) -> Dict:
        """Get status of all loaded models"""
        return {
            'models_loaded': list(self.models.keys()),
            'total_models': len(self.models),
            'ai_service_available': self.ai_service is not None,
            'probability_engine_available': self.probability_engine is not None,
            'openai_api_configured': os.getenv('OPENAI_API_KEY') is not None
        }
