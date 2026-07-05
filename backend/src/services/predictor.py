import os
import joblib
import pandas as pd
import numpy as np
import logging

logger = logging.getLogger(__name__)

class FootballPredictor:
    def __init__(self):
        self.model = None
        # Resolve model path from env or fallback to backend/models/predictor.joblib
        env_model_path = os.getenv('MODEL_PATH')
        if env_model_path:
            # If env provides a relative path, resolve it from backend directory
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
            candidate = env_model_path
            if not os.path.isabs(candidate):
                candidate = os.path.normpath(os.path.join(backend_dir, env_model_path))
            self.model_path = candidate
        else:
            # Fix the path to point to the correct models directory
            backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))
            self.model_path = os.path.join(backend_dir, 'models', 'predictor.joblib')
        self.load_model()

    def load_model(self):
        try:
            if os.path.exists(self.model_path):
                self.model = joblib.load(self.model_path)
                logger.info(f"Model loaded successfully from {self.model_path}")
            else:
                logger.warning(f"Model file not found at {self.model_path}. Using dummy predictions.")
        except Exception as e:
            logger.error(f"Error loading model from {self.model_path}: {str(e)}. Using dummy predictions.")

    def preprocess_features(self, game_data):
        # This is a placeholder for actual feature engineering
        # In a real application, this would involve complex data processing
        features = {
            'home_team_rating': game_data.get('home_team_rating', 1500),
            'away_team_rating': game_data.get('away_team_rating', 1500),
            'home_team_offense_rating': game_data.get('home_offense_rating', 100),
            'away_team_offense_rating': game_data.get('away_offense_rating', 100),
            'home_team_defense_rating': game_data.get('home_defense_rating', 100),
            'away_team_defense_rating': game_data.get('away_defense_rating', 100),
            'home_team_recent_form': game_data.get('home_recent_form', 0.5),
            'away_team_recent_form': game_data.get('away_recent_form', 0.5),
            'weather_impact': game_data.get('weather_impact', 0),
            'home_field_advantage': game_data.get('home_field_advantage', 3.0),
            'injury_impact': game_data.get('injury_impact', 0),
            'rest_days_home': game_data.get('rest_days_home', 7),
            'rest_days_away': game_data.get('rest_days_away', 7),
            'head_to_head_record': game_data.get('h2h_record', 0.5),
            'season_week': game_data.get('week', 1),
            'is_playoff': int(game_data.get('is_playoff', False))
        }
        return pd.DataFrame([features])

    def predict_game(self, game_data):
        features = self.preprocess_features(game_data)
        if self.model is not None:
            try:
                # Assuming binary classification with class 1 = home win
                if hasattr(self.model, 'predict_proba'):
                    proba = self.model.predict_proba(features)[0]
                    # pick the probability for home team win; adjust if label order differs
                    home_win_proba = float(proba[1]) if len(proba) > 1 else float(proba[0])
                else:
                    # If model doesn't support predict_proba, approximate via predict
                    pred = self.model.predict(features)[0]
                    home_win_proba = 0.7 if int(pred) == 1 else 0.3
            except Exception as e:
                logger.error(f"Model inference error: {str(e)}. Falling back to heuristic.")
                home_win_proba = 0.5 + (game_data.get('home_team_rating', 1500) - game_data.get('away_team_rating', 1500)) / 10000
                home_win_proba = max(0.01, min(0.99, home_win_proba))
        else:
            # Fallback to heuristic/dummy when model not loaded
            home_win_proba = 0.5 + (game_data.get('home_team_rating', 1500) - game_data.get('away_team_rating', 1500)) / 10000
            home_win_proba = max(0.01, min(0.99, home_win_proba))

        away_win_proba = 1 - home_win_proba
        draw_proba = 0.0 # Assuming no draws for NFL/NCAAF moneyline

        # Simulate some confidence based on dummy prediction
        confidence = abs(home_win_proba - 0.5) * 2 # Higher confidence for stronger leans

        return {
            'home_win_probability': home_win_proba,
            'away_win_probability': away_win_proba,
            'draw_probability': draw_proba,
            'predicted_winner': game_data['home_team'] if home_win_proba > away_win_proba else game_data['away_team'],
            'confidence': confidence,
            'prediction_source': 'trained_model' if self.model is not None else 'heuristic_fallback'
        }

    def get_feature_names(self):
        # Return expected feature names for the model
        return [
            'home_team_rating', 'away_team_rating',
            'home_team_offense_rating', 'away_team_offense_rating',
            'home_team_defense_rating', 'away_team_defense_rating',
            'home_team_recent_form', 'away_team_recent_form',
            'weather_impact', 'home_field_advantage', 'injury_impact',
            'rest_days_home', 'rest_days_away', 'head_to_head_record',
            'season_week', 'is_playoff'
        ]


    def predict_multiple_games(self, games_data):
        predictions = []
        for game_data in games_data:
            try:
                prediction = self.predict_game(game_data)
                prediction['game_id'] = game_data.get('game_id', 'unknown')
                predictions.append(prediction)
            except Exception as e:
                logger.error(f"Error predicting game {game_data.get('game_id', 'unknown')}: {str(e)}")
                continue
        return predictions


