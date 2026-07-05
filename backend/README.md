# Backend — Football Betting AI API

<div align="center">

[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1%2B-lightgrey)](https://flask.palletsprojects.com/)
[![LightGBM](https://img.shields.io/badge/ML-LightGBM-orange)](https://lightgbm.readthedocs.io/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](../LICENSE)
[![Socket.IO](https://img.shields.io/badge/Realtime-Socket.IO-010101)](https://socket.io/)

**RESTful API backend for the Football Betting AI Prediction System — provides ML-powered predictions, Expected Value calculations, real-time odds fetching, and WebSocket-based live updates.**

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Services](#-services)
- [API Endpoints](#-api-endpoints)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Development](#-development)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

The backend is a **Flask-based Python API server** that serves as the computational engine for the Football Betting AI system. It handles:

- **Machine Learning Inference** — Loading and running LightGBM models to predict game outcomes
- **Expected Value Mathematics** — Calculating EV for moneyline, spread, and totals markets using the Kelly Criterion
- **Real-Time Odds Integration** — Fetching live odds from The Odds API with rate limiting and caching
- **WebSocket Communication** — Real-time updates via Socket.IO for live game data
- **Database Persistence** — SQLite/PostgreSQL storage for user data and game history
- **AI Analysis** — Enhanced analysis using OpenAI API integration for natural language insights

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Multi-Sport Support** | NFL and NCAAF (College Football) |
| **Multiple Betting Markets** | Moneyline, Spread, Totals |
| **Real-Time Updates** | Live odds via WebSocket push |
| **Mock Data Fallback** | Works without API keys using mock data |
| **Rate Limiting** | Built-in API request throttling |
| **Health Monitoring** | Endpoint for load balancer health checks |

---

## 🛠 Tech Stack

| Technology | Purpose |
|------------|---------|
| **Python 3.11+** | Core programming language |
| **Flask 3.1** | Web framework and REST API |
| **Flask-CORS** | Cross-origin resource sharing |
| **Flask-Socket.IO** | WebSocket real-time communication |
| **SQLAlchemy** | ORM for database operations |
| **LightGBM** | Gradient boosting ML model |
| **scikit-learn** | ML utilities and preprocessing |
| **pandas / numpy** | Data manipulation and analysis |
| **joblib** | Model serialization |
| **python-dotenv** | Environment variable management |
| **APScheduler** | Scheduled task execution |
| **Celery + Redis** | Asynchronous task queue |
| **requests** | HTTP client for external APIs |

---

## 📁 Project Structure

```
backend/
│
├── src/                              # Application source code
│   ├── main.py                       # Flask entry point, blueprint registration
│   ├── __init__.py                   # Package initialization
│   │
│   ├── routes/                       # API route handlers (blueprints)
│   │   ├── betting.py                # Core betting prediction endpoints
│   │   ├── enhanced_betting.py       # Advanced EV and analysis endpoints
│   │   ├── espn_style.py             # ESPN-style scoreboard data endpoints
│   │   ├── realtime_betting.py       # WebSocket real-time betting routes
│   │   └── user.py                   # User management and authentication
│   │
│   ├── services/                     # Business logic layer
│   │   ├── predictor.py              # LightGBM model inference engine
│   │   ├── enhanced_predictor.py     # Enhanced multi-model prediction
│   │   ├── ev_calculator.py          # Expected Value mathematics
│   │   ├── advanced_ev_calculator.py # Advanced EV with correlation analysis
│   │   ├── api_fetcher.py            # The Odds API integration client
│   │   ├── probability_engine.py     # Probability distribution modeling
│   │   ├── ai_analysis_service.py    # OpenAI-powered analysis service
│   │   ├── live_betting_engine.py    # Live in-play betting engine
│   │   └── realtime_service.py       # Socket.IO real-time data service
│   │
│   ├── models/                       # SQLAlchemy database models
│   │   └── user.py                   # User model (authentication, preferences)
│   │
│   ├── database/                     # SQLite database files
│   │   └── app.db                    # Local development database
│   │
│   └── static/                       # Static file serving
│       ├── index.html                # Fallback frontend page
│       └── favicon.ico               # Site favicon
│
├── models/                           # Trained ML model files
│   └── predictor.joblib              # LightGBM serialized model
│
├── requirements.txt                  # Python dependency manifest
├── .env.example                      # Environment variable template
├── .env                              # Local credentials (gitignored)
├── .gitignore                        # Git exclusion rules
└── README.md                         # This file
```

---

## ⚙️ Services

### Predictor Service (`predictor.py`)

The core ML inference engine that loads a **LightGBM** model and generates game outcome predictions.

```python
from src.services.predictor import FootballPredictor

predictor = FootballPredictor()
result = predictor.predict_game({
    "home_team": "Kansas City Chiefs",
    "away_team": "Buffalo Bills",
    "home_team_rating": 1600,
    "away_team_rating": 1580
})
# Returns: { home_win_probability, away_win_probability, confidence, ... }
```

**Features:**
- Model loading with automatic fallback to heuristic predictions
- 16 engineered features (ELO ratings, offense/defense metrics, recent form, etc.)
- Multiple game prediction support via `predict_multiple_games()`
- Confidence scoring based on prediction certainty

### EV Calculator (`ev_calculator.py`)

Performs Expected Value calculations across all betting markets using the Kelly Criterion.

| Method | Purpose |
|--------|---------|
| `calculate_ev()` | Core EV calculation for any bet |
| `calculate_moneyline_ev()` | Moneyline market analysis |
| `calculate_spread_ev()` | Point spread market analysis |
| `calculate_total_ev()` | Over/under total market analysis |
| `calculate_kelly_criterion()` | Optimal bet sizing |
| `find_best_bets()` | Identify highest EV opportunities |
| `generate_betting_summary()` | Comprehensive game betting report |

### Odds Fetcher (`api_fetcher.py`)

Handles integration with **The Odds API** for real-time sportsbook odds.

```python
from src.services.api_fetcher import OddsFetcher

fetcher = OddsFetcher()
odds = fetcher.get_odds(sport="nfl", markets=["moneyline", "spread", "totals"])
best = fetcher.get_best_odds(odds)  # Find best prices across sportsbooks
upcoming = fetcher.get_upcoming_games(sport="nfl", days_ahead=7)
```

**Features:**
- Rate-limited API requests to respect provider limits
- Automatic mock data fallback when API key is not configured
- Best odds aggregation across multiple sportsbooks
- Date-filtered upcoming game queries
- Supports NFL and NCAAF sports keys

### Additional Services

| Service | File | Purpose |
|---------|------|---------|
| **Enhanced Predictor** | `enhanced_predictor.py` | Multi-model ensemble predictions |
| **Advanced EV Calculator** | `advanced_ev_calculator.py` | EV with correlation and variance analysis |
| **Probability Engine** | `probability_engine.py` | Statistical distribution modeling |
| **AI Analysis Service** | `ai_analysis_service.py` | OpenAI GPT integration for game analysis |
| **Live Betting Engine** | `live_betting_engine.py` | In-play betting opportunity detection |
| **Realtime Service** | `realtime_service.py` | Socket.IO event broadcasting |

---

## 🔌 API Endpoints

### Base URL: `http://localhost:5000/api/`

### Betting Routes (`/betting/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/betting/odds` | Fetch real-time odds for NFL/NCAAF |
| POST | `/betting/predict` | Generate ML predictions for a game |
| POST | `/betting/analyze` | Comprehensive game analysis with odds |
| GET | `/betting/upcoming` | Get upcoming games with optional predictions |
| GET | `/betting/health` | Health check endpoint |

### Enhanced Routes (`/enhanced/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/enhanced/analyze` | Advanced analysis with AI insights |
| POST | `/enhanced/predict` | Multi-model ensemble predictions |

### ESPN Routes (`/espn/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/espn/scoreboard` | ESPN-style scoreboard with live scores |
| GET | `/espn/upcoming` | Upcoming games with team data |

### User Routes (`/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/register` | User registration |
| POST | `/login` | User authentication |

### Realtime Routes (`/realtime/`)

| Method | Endpoint | Description |
|--------|----------|-------------|
| WebSocket | `/realtime/odds` | Live odds streaming |
| WebSocket | `/realtime/games` | Live game updates |

---

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- pip (Python package manager)

### Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API credentials

# Run the server
python src/main.py
```

The server will start at **http://localhost:5000**.

---

## 🔑 Configuration

### Environment Variables (`backend/.env`)

```env
# ─── API Configuration ──────────────────────────────────────────
API_KEY=your_odds_api_key_here
ODDS_API_BASE_URL=https://api.the-odds-api.com/v4
ODDS_API_KEY=your_odds_api_key_here

# ─── Model Configuration ────────────────────────────────────────
MODEL_PATH=./models/predictor.joblib

# ─── Flask Application ──────────────────────────────────────────
FLASK_ENV=development
SECRET_KEY=your-secret-key-change-in-production
LOG_LEVEL=DEBUG

# ─── Database ───────────────────────────────────────────────────
DATABASE_URL=sqlite:///app.db

# ─── Redis (for Celery) ────────────────────────────────────────
REDIS_URL=redis://localhost:6379/0

# ─── OpenAI (optional — for AI analysis) ──────────────────────
OPENAI_API_KEY=your_openai_api_key
```

### Working Without API Keys

The backend includes **mock data fallbacks** for all external API integrations:

- **The Odds API**: Returns simulated NFL/NCAAF odds for 2 sample games
- **ML Model**: Uses heuristic predictions if `predictor.joblib` is not present
- **OpenAI**: AI analysis features gracefully degrade without an API key

This means the application is fully functional for development and testing without any external credentials.

---

## 💻 Development

### Running in Development Mode

```bash
python src/main.py
# Server starts on http://0.0.0.0:5000 with debug mode enabled
```

### Testing API Endpoints

```bash
# Health check
curl http://localhost:5000/api/betting/health

# Fetch NFL odds
curl "http://localhost:5000/api/betting/odds?sport=nfl"

# Generate prediction
curl -X POST http://localhost:5000/api/betting/predict \
  -H "Content-Type: application/json" \
  -d '{
    "game_data": {
      "home_team": "Kansas City Chiefs",
      "away_team": "Buffalo Bills"
    },
    "odds_data": {
      "moneyline": {"home": -120, "away": +100}
    },
    "bankroll": 1000
  }'

# ESPN scoreboard
curl http://localhost:5000/api/espn/scoreboard
```

### Real-Time WebSocket

The backend supports WebSocket connections via **Socket.IO** for live game updates:

```javascript
// Client-side connection (React/Frontend)
import { io } from 'socket.io-client';

const socket = io('http://localhost:5000', {
  transports: ['websocket', 'polling']
});

socket.on('connect', () => console.log('Connected to realtime service'));
socket.on('odds_update', (data) => console.log('New odds:', data));
socket.on('game_update', (data) => console.log('Game update:', data));
```

---

## 🌐 Deployment

### Production Server

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn (4 workers)
gunicorn -w 4 -b 0.0.0.0:5000 src.main:app

# With eventlet for WebSocket support
gunicorn -k eventlet -w 1 -b 0.0.0.0:5000 src.main:app
```

### Docker (Recommended for Production)

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 5000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "src.main:app"]
```

### Database Migration

```bash
# For production, configure PostgreSQL via DATABASE_URL:
# postgresql://user:password@host:5432/football_betting

# SQLAlchemy handles table creation automatically via:
# db.create_all()
```

---

## 📊 ML Model Details

### Current Model: LightGBM

- **Features**: 16 engineered features (ELO ratings, form, injuries, weather, etc.)
- **Accuracy**: ~65-70% on historical NFL data
- **AUC-ROC**: ~0.72
- **Fallback**: Heuristic predictions when model file is unavailable

### Training a New Model

1. Collect historical game data with features
2. Train with LightGBM: `lgb.train(params, train_data)`
3. Save: `joblib.dump(model, 'models/predictor.joblib')`
4. Restart the backend server

---

## 🧪 Testing

```bash
# Run tests (if available)
python -m pytest tests/

# Test model loading
python -c "from src.services.predictor import FootballPredictor; p = FootballPredictor(); print('Model loaded:', p.model is not None)"

# Test odds fetcher
python -c "from src.services.api_fetcher import OddsFetcher; f = OddsFetcher(); print('Mock odds:', f.get_odds('nfl'))"
```

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Ensure existing functionality works
5. Commit and push
6. Open a Pull Request

### Areas for Contribution

- Enhanced feature engineering for the ML model
- Additional sportsbook API integrations
- New betting market support (player props, futures)
- Performance optimizations and caching
- Unit and integration test coverage
- API documentation improvements

---

## 📄 License

This project is licensed under the **Apache License, Version 2.0**. See the [LICENSE](../LICENSE) file for details.

---

<div align="center">
  <sub>Built with ❤️ for responsible sports betting analysis</sub>
  <br>
  <sub>Backend API v1.0.0</sub>
</div>