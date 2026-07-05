import os
import requests
import time
from typing import Dict, List, Optional, Union
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

class OddsFetcher:
    def __init__(self):
        self.odds_api_key = os.getenv("ODDS_API_KEY")
        self.odds_api_base = os.getenv("ODDS_API_BASE_URL", "https://api.the-odds-api.com/v4")
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Football-Betting-AI/1.0"
        })
        
        self.last_request_time = 0
        self.min_request_interval = 1.0
        
        self.sports = {
            "nfl": "americanfootball_nfl",
            "ncaaf": "americanfootball_ncaaf"
        }
        
        self.markets = {
            "moneyline": "h2h",
            "spread": "spreads",
            "totals": "totals"
        }
    
    def _rate_limit(self):
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _make_request(self, url: str, params: Dict = None) -> Optional[Dict]:
        self._rate_limit()
        
        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            
            remaining = response.headers.get("x-requests-remaining")
            if remaining:
                logger.info(f"API requests remaining: {remaining}")
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {str(e)}")
            return None
        except ValueError as e:
            logger.error(f"Failed to parse API response: {str(e)}")
            return None
    
    def get_sports(self) -> List[Dict]:
        if not self.odds_api_key:
            logger.warning("No API key provided, returning mock data")
            return self._get_mock_sports()
        
        url = f"{self.odds_api_base}/sports"
        params = {"apiKey": self.odds_api_key}
        
        data = self._make_request(url, params)
        return data if data else self._get_mock_sports()
    
    def get_odds(self, sport: str = "nfl", markets: List[str] = None, 
                 regions: List[str] = None) -> List[Dict]:
        if not self.odds_api_key:
            logger.warning("No API key provided, returning mock data")
            return self._get_mock_odds(sport)
        
        markets = markets or ["moneyline", "spread", "totals"]
        regions = regions or ["us"]
        
        sport_key = self.sports.get(sport, sport)
        market_keys = [self.markets.get(m, m) for m in markets]
        
        url = f"{self.odds_api_base}/sports/{sport_key}/odds"
        params = {
            "apiKey": self.odds_api_key,
            "regions": ",".join(regions),
            "markets": ",".join(market_keys),
            "oddsFormat": "american",
            "dateFormat": "iso"
        }
        
        data = self._make_request(url, params)
        
        if data:
            return self._process_odds_data(data)
        else:
            return self._get_mock_odds(sport)
    
    def get_game_odds(self, game_id: str, sport: str = "nfl") -> Optional[Dict]:
        all_odds = self.get_odds(sport)
        
        for game in all_odds:
            if game.get("id") == game_id:
                return game
        
        return None
    
    def _process_odds_data(self, raw_data: List[Dict]) -> List[Dict]:
        processed_games = []
        
        for game in raw_data:
            try:
                processed_game = {
                    "id": game.get("id"),
                    "sport_key": game.get("sport_key"),
                    "sport_title": game.get("sport_title"),
                    "commence_time": game.get("commence_time"),
                    "home_team": game.get("home_team"),
                    "away_team": game.get("away_team"),
                    "bookmakers": []
                }
                
                for bookmaker in game.get("bookmakers", []):
                    processed_bookmaker = {
                        "key": bookmaker.get("key"),
                        "title": bookmaker.get("title"),
                        "last_update": bookmaker.get("last_update"),
                        "markets": {}
                    }
                    
                    for market in bookmaker.get("markets", []):
                        market_key = market.get("key")
                        market_data = {
                            "last_update": market.get("last_update"),
                            "outcomes": []
                        }
                        
                        for outcome in market.get("outcomes", []):
                            outcome_data = {
                                "name": outcome.get("name"),
                                "price": outcome.get("price"),
                                "point": outcome.get("point")
                            }
                            market_data["outcomes"].append(outcome_data)
                        
                        processed_bookmaker["markets"][market_key] = market_data
                    
                    processed_game["bookmakers"].append(processed_bookmaker)
                
                processed_games.append(processed_game)
                
            except Exception as e:
                logger.error(f"Error processing game data: {str(e)}")
                continue
        
        return processed_games
    
    def get_best_odds(self, games_data: List[Dict]) -> List[Dict]:
        best_odds_games = []
        
        for game in games_data:
            best_game = {
                "id": game.get("id"),
                "sport_key": game.get("sport_key"),
                "commence_time": game.get("commence_time"),
                "home_team": game.get("home_team"),
                "away_team": game.get("away_team"),
                "best_odds": {}
            }
            
            best_odds = {
                "moneyline": {"home": None, "away": None},
                "spread": {"home": None, "away": None, "line": None},
                "totals": {"over": None, "under": None, "line": None}
            }
            
            for bookmaker in game.get("bookmakers", []):
                markets = bookmaker.get("markets", {})
                
                if "h2h" in markets:
                    for outcome in markets["h2h"].get("outcomes", []):
                        team = outcome.get("name")
                        price = outcome.get("price")
                        
                        if team == game["home_team"]:
                            if not best_odds["moneyline"]["home"] or price > best_odds["moneyline"]["home"]:
                                best_odds["moneyline"]["home"] = price
                        elif team == game["away_team"]:
                            if not best_odds["moneyline"]["away"] or price > best_odds["moneyline"]["away"]:
                                best_odds["moneyline"]["away"] = price
                
                if "spreads" in markets:
                    for outcome in markets["spreads"].get("outcomes", []):
                        team = outcome.get("name")
                        price = outcome.get("price")
                        point = outcome.get("point")
                        
                        if team == game["home_team"]:
                            if not best_odds["spread"]["home"] or price > best_odds["spread"]["home"]:
                                best_odds["spread"]["home"] = price
                                best_odds["spread"]["line"] = point
                        elif team == game["away_team"]:
                            if not best_odds["spread"]["away"] or price > best_odds["spread"]["away"]:
                                best_odds["spread"]["away"] = price
                
                if "totals" in markets:
                    for outcome in markets["totals"].get("outcomes", []):
                        name = outcome.get("name")
                        price = outcome.get("price")
                        point = outcome.get("point")
                        
                        if name == "Over":
                            if not best_odds["totals"]["over"] or price > best_odds["totals"]["over"]:
                                best_odds["totals"]["over"] = price
                                best_odds["totals"]["line"] = point
                        elif name == "Under":
                            if not best_odds["totals"]["under"] or price > best_odds["totals"]["under"]:
                                best_odds["totals"]["under"] = price
            
            best_game["best_odds"] = best_odds
            best_odds_games.append(best_game)
        
        return best_odds_games
    
    def _get_mock_sports(self) -> List[Dict]:
        return [
            {
                "key": "americanfootball_nfl",
                "group": "American Football",
                "title": "NFL",
                "description": "US National Football League",
                "active": True,
                "has_outrights": False
            },
            {
                "key": "americanfootball_ncaaf",
                "group": "American Football",
                "title": "NCAAF",
                "description": "US College Football",
                "active": True,
                "has_outrights": False
            }
        ]
    
    def _get_mock_odds(self, sport: str) -> List[Dict]:
        base_time = datetime.now() + timedelta(days=1)
        
        mock_games = [
            {
                "id": "mock_game_1",
                "sport_key": self.sports.get(sport, sport),
                "commence_time": base_time.isoformat(),
                "home_team": "Kansas City Chiefs",
                "away_team": "Buffalo Bills",
                "best_odds": {
                    "moneyline": {"home": -120, "away": +100},
                    "spread": {"home": -110, "away": -110, "line": -2.5},
                    "totals": {"over": -110, "under": -110, "line": 47.5}
                }
            },
            {
                "id": "mock_game_2",
                "sport_key": self.sports.get(sport, sport),
                "commence_time": (base_time + timedelta(hours=3)).isoformat(),
                "home_team": "Dallas Cowboys",
                "away_team": "Philadelphia Eagles",
                "best_odds": {
                    "moneyline": {"home": +150, "away": -180},
                    "spread": {"home": -110, "away": -110, "line": +3.5},
                    "totals": {"over": -105, "under": -115, "line": 44.5}
                }
            }
        ]
        
        return mock_games
    
    def get_upcoming_games(self, sport: str = "nfl", days_ahead: int = 7) -> List[Dict]:
        all_odds = self.get_odds(sport)
        upcoming_games = []
        
        now_utc = datetime.now(timezone.utc)
        cutoff_time = now_utc + timedelta(days=days_ahead)
        
        for game in all_odds:
            try:
                game_time_str = game["commence_time"]
                # Ensure timezone-aware datetime parsing
                if game_time_str.endswith('Z'):
                    game_time = datetime.fromisoformat(game_time_str.replace("Z", "+00:00"))
                elif '+' in game_time_str or game_time_str.endswith('00:00'):
                    game_time = datetime.fromisoformat(game_time_str)
                else:
                    # If no timezone info, assume UTC
                    game_time = datetime.fromisoformat(game_time_str).replace(tzinfo=timezone.utc)
                
                # Ensure game_time is timezone-aware
                if game_time.tzinfo is None:
                    game_time = game_time.replace(tzinfo=timezone.utc)
                
                if game_time > now_utc and game_time <= cutoff_time:
                    upcoming_games.append(game)
            except (ValueError, KeyError) as e:
                logger.warning(f"Error parsing game time for game {game.get('id', 'unknown')}: {str(e)}")
                continue
        
        upcoming_games.sort(key=lambda x: x.get("commence_time", ""))
        
        return upcoming_games


