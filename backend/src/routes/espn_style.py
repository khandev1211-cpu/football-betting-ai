from flask import Blueprint, jsonify, request
import requests
import os
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any

espn_style_bp = Blueprint('espn_style', __name__)

class ESPNStyleDataFetcher:
    def __init__(self):
        self.odds_api_key = os.getenv("ODDS_API_KEY")
        self.odds_api_base = os.getenv("ODDS_API_BASE_URL", "https://api.the-odds-api.com/v4")
        
    def fetch_games_data(self, sport_key: str, days_from: int = 3) -> List[Dict[str, Any]]:
        """Fetch both scores and odds data for a specific sport"""
        if not self.odds_api_key:
            return []
        
        all_games = []
        
        # Fetch completed/live games from scores endpoint
        scores_url = f"{self.odds_api_base}/sports/{sport_key}/scores/"
        scores_params = {
            'apiKey': self.odds_api_key,
            'daysFrom': days_from
        }
        
        try:
            response = requests.get(scores_url, params=scores_params, timeout=10)
            response.raise_for_status()
            scores_data = response.json()
            print(f"Raw scores API response for {sport_key}: {len(scores_data)} games")
            
            # Debug: Print sample game data
            if scores_data:
                sample_game = scores_data[0]
                print(f"Sample game data: {sample_game}")
                print(f"Game completed status: {sample_game.get('completed', 'N/A')}")
                print(f"Game scores: {sample_game.get('scores', 'N/A')}")
            
            all_games.extend(scores_data)
            print(f"Fetched {len(scores_data)} games from scores endpoint for {sport_key}")
        except requests.RequestException as e:
            print(f"Error fetching {sport_key} scores: {e}")
            print(f"Scores URL: {scores_url}")
            print(f"Scores params: {scores_params}")
        
        # Fetch upcoming games from odds endpoint (only next 10 days)
        odds_url = f"{self.odds_api_base}/sports/{sport_key}/odds/"
        odds_params = {
            'apiKey': self.odds_api_key,
            'regions': 'us',
            'markets': 'h2h',
            'oddsFormat': 'american'
        }
        
        try:
            response = requests.get(odds_url, params=odds_params, timeout=10)
            response.raise_for_status()
            odds_data = response.json()
            
            # Filter games to only next 10 days
            current_time = datetime.now(timezone.utc)
            ten_days_from_now = current_time + timedelta(days=10)
            
            filtered_odds_data = []
            for game in odds_data:
                if game.get('commence_time'):
                    try:
                        game_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                        if current_time <= game_time <= ten_days_from_now:
                            filtered_odds_data.append(game)
                    except:
                        pass
            
            # Filter out games that are already in scores data (to avoid duplicates)
            existing_ids = {game.get('id') for game in all_games}
            upcoming_games = [game for game in filtered_odds_data if game.get('id') not in existing_ids]
            all_games.extend(upcoming_games)
            print(f"Fetched {len(upcoming_games)} upcoming games (within 10 days) from odds endpoint for {sport_key}")
            
        except requests.RequestException as e:
            print(f"Error fetching {sport_key} odds: {e}")
        
        print(f"Total games for {sport_key}: {len(all_games)}")
        return all_games
    
    def categorize_games(self, games: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Categorize games into live, upcoming, and completed"""
        live_games = []
        upcoming_games = []
        completed_games = []
        
        print(f"Categorizing {len(games)} games...")
        
        for game in games:
            # Parse game data
            game_data = {
                'id': game.get('id'),
                'sport_key': game.get('sport_key'),
                'sport_title': game.get('sport_title'),
                'home_team': game.get('home_team'),
                'away_team': game.get('away_team'),
                'commence_time': game.get('commence_time'),
                'completed': game.get('completed', False),
                'scores': game.get('scores'),
                'last_update': game.get('last_update')
            }
            
            # Add formatted time
            if game_data['commence_time']:
                try:
                    dt = datetime.fromisoformat(game_data['commence_time'].replace('Z', '+00:00'))
                    game_data['formatted_time'] = dt.strftime('%m/%d %I:%M %p')
                    game_data['date'] = dt.strftime('%Y-%m-%d')
                except:
                    game_data['formatted_time'] = 'TBD'
                    game_data['date'] = 'TBD'
            
            # Categorize based on status and time
            current_time = datetime.now(timezone.utc)
            game_time = None
            
            if game_data['commence_time']:
                try:
                    game_time = datetime.fromisoformat(game_data['commence_time'].replace('Z', '+00:00'))
                except:
                    pass
            
            # Debug logging
            print(f"Game: {game_data['away_team']} @ {game_data['home_team']}")
            print(f"  Completed flag: {game_data['completed']}")
            print(f"  Has scores: {bool(game_data['scores'])}")
            print(f"  Game time: {game_time}")
            print(f"  Current time: {current_time}")
            
            if game_data['completed']:
                # Completed game
                print(f"  -> COMPLETED game")
                if game_data['scores']:
                    home_score = next((s['score'] for s in game_data['scores'] if s['name'] == game_data['home_team']), '0')
                    away_score = next((s['score'] for s in game_data['scores'] if s['name'] == game_data['away_team']), '0')
                    game_data['home_score'] = home_score
                    game_data['away_score'] = away_score
                    game_data['status'] = 'FINAL'
                    print(f"  Scores: {game_data['away_team']} {away_score} - {game_data['home_team']} {home_score}")
                completed_games.append(game_data)
            elif game_data['scores'] and not game_data['completed']:
                # Check if this is actually a completed game mismarked as not completed
                home_score = next((s['score'] for s in game_data['scores'] if s['name'] == game_data['home_team']), '0')
                away_score = next((s['score'] for s in game_data['scores'] if s['name'] == game_data['away_team']), '0')
                
                # If scores are non-zero and game time is more than 4 hours ago, it's likely completed
                if game_time and current_time > game_time:
                    time_diff = (current_time - game_time).total_seconds() / 3600  # hours
                    print(f"  Time since game start: {time_diff:.1f} hours")
                    
                    if time_diff > 4:  # Game started more than 4 hours ago with scores = completed
                        game_data['home_score'] = home_score
                        game_data['away_score'] = away_score
                        game_data['status'] = 'FINAL'
                        game_data['completed'] = True  # Force completion
                        print(f"  -> COMPLETED game (forced): {game_data['away_team']} {away_score} - {game_data['home_team']} {home_score}")
                        completed_games.append(game_data)
                    else:
                        # Game started recently with scores = live
                        game_data['home_score'] = home_score
                        game_data['away_score'] = away_score
                        game_data['status'] = 'LIVE'
                        print(f"  -> LIVE game: {game_data['away_team']} {away_score} - {game_data['home_team']} {home_score}")
                        live_games.append(game_data)
                else:
                    # Has scores but game hasn't started yet = upcoming
                    game_data['home_score'] = None
                    game_data['away_score'] = None
                    game_data['status'] = 'SCHEDULED'
                    print(f"  -> UPCOMING game (has odds but not started)")
                    upcoming_games.append(game_data)
            else:
                # No scores, not completed = UPCOMING
                game_data['home_score'] = None
                game_data['away_score'] = None
                game_data['status'] = 'SCHEDULED'
                print(f"  -> UPCOMING game (no scores)")
                upcoming_games.append(game_data)
        
        print(f"Categorization complete:")
        print(f"  Live games: {len(live_games)}")
        print(f"  Upcoming games: {len(upcoming_games)}")
        print(f"  Completed games: {len(completed_games)}")
        
        return {
            'live': live_games,
            'upcoming': upcoming_games,
            'completed': completed_games
        }
    
    def get_combined_football_data(self, days_from: int = 14) -> Dict[str, Any]:
        """Get combined NFL and NCAAF data in ESPN style"""
        # Fetch data from both leagues
        nfl_games = self.fetch_games_data('americanfootball_nfl', days_from)
        ncaaf_games = self.fetch_games_data('americanfootball_ncaaf', days_from)
        
        # Categorize games
        nfl_categorized = self.categorize_games(nfl_games)
        ncaaf_categorized = self.categorize_games(ncaaf_games)
        
        # Filter out old completed games (only show completed games from last 24 hours)
        current_time = datetime.now(timezone.utc)
        
        # Filter completed games to only recent ones
        filtered_nfl_completed = []
        for game in nfl_categorized['completed']:
            if game.get('commence_time'):
                try:
                    game_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                    hours_since_game = (current_time - game_time).total_seconds() / 3600
                    if hours_since_game <= 24:  # Only show games completed in last 24 hours
                        filtered_nfl_completed.append(game)
                except:
                    pass
        
        filtered_ncaaf_completed = []
        for game in ncaaf_categorized['completed']:
            if game.get('commence_time'):
                try:
                    game_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                    hours_since_game = (current_time - game_time).total_seconds() / 3600
                    if hours_since_game <= 24:  # Only show games completed in last 24 hours
                        filtered_ncaaf_completed.append(game)
                except:
                    pass
        
        nfl_categorized['completed'] = filtered_nfl_completed
        ncaaf_categorized['completed'] = filtered_ncaaf_completed
        
        # Filter upcoming games to only next 10 days
        ten_days_from_now = current_time + timedelta(days=10)
        
        filtered_nfl_upcoming = []
        for game in nfl_categorized['upcoming']:
            if game.get('commence_time'):
                try:
                    game_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                    if current_time <= game_time <= ten_days_from_now:
                        filtered_nfl_upcoming.append(game)
                except:
                    pass
        
        filtered_ncaaf_upcoming = []
        for game in ncaaf_categorized['upcoming']:
            if game.get('commence_time'):
                try:
                    game_time = datetime.fromisoformat(game['commence_time'].replace('Z', '+00:00'))
                    if current_time <= game_time <= ten_days_from_now:
                        filtered_ncaaf_upcoming.append(game)
                except:
                    pass
        
        nfl_categorized['upcoming'] = filtered_nfl_upcoming
        ncaaf_categorized['upcoming'] = filtered_ncaaf_upcoming
        
        # Combine data
        combined_data = {
            'live': {
                'nfl': nfl_categorized['live'],
                'ncaaf': ncaaf_categorized['live'],
                'total': len(nfl_categorized['live']) + len(ncaaf_categorized['live'])
            },
            'upcoming': {
                'nfl': nfl_categorized['upcoming'],
                'ncaaf': ncaaf_categorized['upcoming'],
                'total': len(nfl_categorized['upcoming']) + len(ncaaf_categorized['upcoming'])
            },
            'completed': {
                'nfl': nfl_categorized['completed'],
                'ncaaf': ncaaf_categorized['completed'],
                'total': len(nfl_categorized['completed']) + len(ncaaf_categorized['completed'])
            },
            'summary': {
                'total_games': len(nfl_games) + len(ncaaf_games),
                'nfl_games': len(nfl_games),
                'ncaaf_games': len(ncaaf_games),
                'live_games': len(nfl_categorized['live']) + len(ncaaf_categorized['live']),
                'upcoming_games': len(nfl_categorized['upcoming']) + len(ncaaf_categorized['upcoming']),
                'completed_games': len(nfl_categorized['completed']) + len(ncaaf_categorized['completed'])
            }
        }
        
        return combined_data
    
    def _create_mock_completed_games(self) -> Dict[str, List[Dict[str, Any]]]:
        """Create mock completed games for demonstration when no real data is available"""
        from datetime import datetime, timedelta
        
        yesterday = datetime.now() - timedelta(days=1)
        two_days_ago = datetime.now() - timedelta(days=2)
        
        mock_nfl_games = [
            {
                'id': 'mock_nfl_completed_1',
                'sport_key': 'americanfootball_nfl',
                'sport_title': 'NFL',
                'home_team': 'Kansas City Chiefs',
                'away_team': 'Buffalo Bills',
                'commence_time': yesterday.isoformat(),
                'completed': True,
                'home_score': 24,
                'away_score': 21,
                'status': 'FINAL',
                'formatted_time': yesterday.strftime('%m/%d %I:%M %p'),
                'date': yesterday.strftime('%Y-%m-%d')
            },
            {
                'id': 'mock_nfl_completed_2',
                'sport_key': 'americanfootball_nfl',
                'sport_title': 'NFL',
                'home_team': 'Dallas Cowboys',
                'away_team': 'Philadelphia Eagles',
                'commence_time': two_days_ago.isoformat(),
                'completed': True,
                'home_score': 17,
                'away_score': 20,
                'status': 'FINAL',
                'formatted_time': two_days_ago.strftime('%m/%d %I:%M %p'),
                'date': two_days_ago.strftime('%Y-%m-%d')
            }
        ]
        
        mock_ncaaf_games = [
            {
                'id': 'mock_ncaaf_completed_1',
                'sport_key': 'americanfootball_ncaaf',
                'sport_title': 'NCAAF',
                'home_team': 'Alabama Crimson Tide',
                'away_team': 'Georgia Bulldogs',
                'commence_time': yesterday.isoformat(),
                'completed': True,
                'home_score': 28,
                'away_score': 14,
                'status': 'FINAL',
                'formatted_time': yesterday.strftime('%m/%d %I:%M %p'),
                'date': yesterday.strftime('%Y-%m-%d')
            }
        ]
        
        return {
            'nfl': mock_nfl_games,
            'ncaaf': mock_ncaaf_games
        }
    
    def _create_mock_live_games(self) -> Dict[str, List[Dict[str, Any]]]:
        """Create mock live games for demonstration when no real live data is available"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        mock_nfl_games = [
            {
                'id': 'mock_nfl_live_1',
                'sport_key': 'americanfootball_nfl',
                'sport_title': 'NFL',
                'home_team': 'Kansas City Chiefs',
                'away_team': 'Buffalo Bills',
                'home_score': '21',
                'away_score': '17',
                'status': 'LIVE',
                'commence_time': now.isoformat(),
                'formatted_time': 'LIVE',
                'date': now.strftime('%Y-%m-%d'),
                'completed': False,
                'scores': [
                    {'name': 'Kansas City Chiefs', 'score': '21'},
                    {'name': 'Buffalo Bills', 'score': '17'}
                ],
                'last_update': now.isoformat(),
                'quarter': '3rd Quarter',
                'time_remaining': '8:42'
            },
            {
                'id': 'mock_nfl_live_2',
                'sport_key': 'americanfootball_nfl',
                'sport_title': 'NFL',
                'home_team': 'Dallas Cowboys',
                'away_team': 'Philadelphia Eagles',
                'home_score': '14',
                'away_score': '10',
                'status': 'LIVE',
                'commence_time': now.isoformat(),
                'formatted_time': 'LIVE',
                'date': now.strftime('%Y-%m-%d'),
                'completed': False,
                'scores': [
                    {'name': 'Dallas Cowboys', 'score': '14'},
                    {'name': 'Philadelphia Eagles', 'score': '10'}
                ],
                'last_update': now.isoformat(),
                'quarter': '2nd Quarter',
                'time_remaining': '3:15'
            }
        ]
        
        mock_ncaaf_games = [
            {
                'id': 'mock_ncaaf_live_1',
                'sport_key': 'americanfootball_ncaaf',
                'sport_title': 'NCAAF',
                'home_team': 'Alabama Crimson Tide',
                'away_team': 'Georgia Bulldogs',
                'home_score': '28',
                'away_score': '24',
                'status': 'LIVE',
                'commence_time': now.isoformat(),
                'formatted_time': 'LIVE',
                'date': now.strftime('%Y-%m-%d'),
                'completed': False,
                'scores': [
                    {'name': 'Alabama Crimson Tide', 'score': '28'},
                    {'name': 'Georgia Bulldogs', 'score': '24'}
                ],
                'last_update': now.isoformat(),
                'quarter': '4th Quarter',
                'time_remaining': '12:30'
            }
        ]
        
        return {
            'nfl': mock_nfl_games,
            'ncaaf': mock_ncaaf_games
        }
    
    def _create_mock_upcoming_games(self) -> Dict[str, List[Dict[str, Any]]]:
        """Create mock upcoming games for demonstration when no real upcoming data is available"""
        from datetime import datetime, timedelta
        
        now = datetime.now()
        
        mock_nfl_games = [
            {
                'id': 'mock_nfl_upcoming_1',
                'sport_key': 'americanfootball_nfl',
                'sport_title': 'NFL',
                'home_team': 'Green Bay Packers',
                'away_team': 'Chicago Bears',
                'home_score': None,
                'away_score': None,
                'status': 'SCHEDULED',
                'commence_time': (now + timedelta(days=2)).isoformat(),
                'formatted_time': (now + timedelta(days=2)).strftime('%m/%d %I:%M %p'),
                'date': (now + timedelta(days=2)).strftime('%Y-%m-%d'),
                'completed': False,
                'scores': None,
                'last_update': now.isoformat()
            },
            {
                'id': 'mock_nfl_upcoming_2',
                'sport_key': 'americanfootball_nfl',
                'sport_title': 'NFL',
                'home_team': 'San Francisco 49ers',
                'away_team': 'Seattle Seahawks',
                'home_score': None,
                'away_score': None,
                'status': 'SCHEDULED',
                'commence_time': (now + timedelta(days=3)).isoformat(),
                'formatted_time': (now + timedelta(days=3)).strftime('%m/%d %I:%M %p'),
                'date': (now + timedelta(days=3)).strftime('%Y-%m-%d'),
                'completed': False,
                'scores': None,
                'last_update': now.isoformat()
            },
            {
                'id': 'mock_nfl_upcoming_3',
                'sport_key': 'americanfootball_nfl',
                'sport_title': 'NFL',
                'home_team': 'Denver Broncos',
                'away_team': 'Las Vegas Raiders',
                'home_score': None,
                'away_score': None,
                'status': 'SCHEDULED',
                'commence_time': (now + timedelta(days=4)).isoformat(),
                'formatted_time': (now + timedelta(days=4)).strftime('%m/%d %I:%M %p'),
                'date': (now + timedelta(days=4)).strftime('%Y-%m-%d'),
                'completed': False,
                'scores': None,
                'last_update': now.isoformat()
            }
        ]
        
        mock_ncaaf_games = [
            {
                'id': 'mock_ncaaf_upcoming_1',
                'sport_key': 'americanfootball_ncaaf',
                'sport_title': 'NCAAF',
                'home_team': 'Ohio State Buckeyes',
                'away_team': 'Michigan Wolverines',
                'home_score': None,
                'away_score': None,
                'status': 'SCHEDULED',
                'commence_time': (now + timedelta(days=2, hours=3)).isoformat(),
                'formatted_time': (now + timedelta(days=2, hours=3)).strftime('%m/%d %I:%M %p'),
                'date': (now + timedelta(days=2, hours=3)).strftime('%Y-%m-%d'),
                'completed': False,
                'scores': None,
                'last_update': now.isoformat()
            },
            {
                'id': 'mock_ncaaf_upcoming_2',
                'sport_key': 'americanfootball_ncaaf',
                'sport_title': 'NCAAF',
                'home_team': 'Texas Longhorns',
                'away_team': 'Oklahoma Sooners',
                'home_score': None,
                'away_score': None,
                'status': 'SCHEDULED',
                'commence_time': (now + timedelta(days=3, hours=2)).isoformat(),
                'formatted_time': (now + timedelta(days=3, hours=2)).strftime('%m/%d %I:%M %p'),
                'date': (now + timedelta(days=3, hours=2)).strftime('%Y-%m-%d'),
                'completed': False,
                'scores': None,
                'last_update': now.isoformat()
            },
            {
                'id': 'mock_ncaaf_upcoming_3',
                'sport_key': 'americanfootball_ncaaf',
                'sport_title': 'NCAAF',
                'home_team': 'Clemson Tigers',
                'away_team': 'Florida State Seminoles',
                'home_score': None,
                'away_score': None,
                'status': 'SCHEDULED',
                'commence_time': (now + timedelta(days=5)).isoformat(),
                'formatted_time': (now + timedelta(days=5)).strftime('%m/%d %I:%M %p'),
                'date': (now + timedelta(days=5)).strftime('%Y-%m-%d'),
                'completed': False,
                'scores': None,
                'last_update': now.isoformat()
            }
        ]
        
        return {
            'nfl': mock_nfl_games,
            'ncaaf': mock_ncaaf_games
        }

# Initialize the fetcher
espn_fetcher = ESPNStyleDataFetcher()

@espn_style_bp.route('/scoreboard', methods=['GET'])
def get_espn_scoreboard():
    """Get ESPN-style scoreboard with live, upcoming, and completed games"""
    try:
        days_from = request.args.get('days', 7, type=int)
        data = espn_fetcher.get_combined_football_data(days_from)
        
        return jsonify({
            'success': True,
            'data': data,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@espn_style_bp.route('/live', methods=['GET'])
def get_live_games():
    """Get only live games"""
    try:
        days_from = request.args.get('days', 3, type=int)
        data = espn_fetcher.get_combined_football_data(days_from)
        
        return jsonify({
            'success': True,
            'data': data['live'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@espn_style_bp.route('/upcoming', methods=['GET'])
def get_upcoming_games():
    """Get only upcoming games"""
    try:
        days_from = request.args.get('days', 7, type=int)
        data = espn_fetcher.get_combined_football_data(days_from)
        
        return jsonify({
            'success': True,
            'data': data['upcoming'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@espn_style_bp.route('/completed', methods=['GET'])
def get_completed_games():
    """Get only completed games"""
    try:
        days_from = request.args.get('days', 7, type=int)
        data = espn_fetcher.get_combined_football_data(days_from)
        
        return jsonify({
            'success': True,
            'data': data['completed'],
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@espn_style_bp.route('/nfl', methods=['GET'])
def get_nfl_only():
    """Get NFL games only"""
    try:
        days_from = request.args.get('days', 3, type=int)
        nfl_games = espn_fetcher.fetch_scores('americanfootball_nfl', days_from)
        categorized = espn_fetcher.categorize_games(nfl_games)
        
        return jsonify({
            'success': True,
            'data': categorized,
            'summary': {
                'total_games': len(nfl_games),
                'live_games': len(categorized['live']),
                'upcoming_games': len(categorized['upcoming']),
                'completed_games': len(categorized['completed'])
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@espn_style_bp.route('/ncaaf', methods=['GET'])
def get_ncaaf_only():
    """Get NCAAF games only"""
    try:
        days_from = request.args.get('days', 3, type=int)
        ncaaf_games = espn_fetcher.fetch_scores('americanfootball_ncaaf', days_from)
        categorized = espn_fetcher.categorize_games(ncaaf_games)
        
        return jsonify({
            'success': True,
            'data': categorized,
            'summary': {
                'total_games': len(ncaaf_games),
                'live_games': len(categorized['live']),
                'upcoming_games': len(categorized['upcoming']),
                'completed_games': len(categorized['completed'])
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
