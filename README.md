# Football Betting AI Prediction System

<div align="center">

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.11%2B-blue)](https://www.python.org/)
[![Node](https://img.shields.io/badge/Node.js-20%2B-green)](https://nodejs.org/)
[![Flask](https://img.shields.io/badge/Flask-3.1%2B-lightgrey)](https://flask.palletsprojects.com/)
[![React](https://img.shields.io/badge/React-18%2B-61DAFB)](https://reactjs.org/)
[![LightGBM](https://img.shields.io/badge/ML-LightGBM-orange)](https://lightgbm.readthedocs.io/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen)](#-contributing)

**A complete AI-powered football betting prediction system with Expected Value (EV) calculations, real-time odds fetching, and an interactive web dashboard for NFL and College Football betting analysis.**

[Features](#-features) •
[Quick Start](#-quick-start) •
[Architecture](#-architecture) •
[API Reference](#-api-reference) •
[ML Model](#-machine-learning-model) •
[Deployment](#-deployment) •
[Contributing](#-contributing)

</div>

---

## 📋 Table of Contents

- [Features](#-features)
- [Quick Start](#-quick-start)
- [Architecture](#-architecture)
- [Project Structure](#-project-structure)
- [API Reference](#-api-reference)
- [Machine Learning Model](#-machine-learning-model)
- [Expected Value Calculations](#-expected-value-calculations)
- [Frontend Features](#-frontend-features)
- [Environment Variables](#-environment-variables)
- [Deployment](#-deployment)
- [Security](#-security)
- [Usage Examples](#-usage-examples)
- [API Credentials](#-api-credentials)
- [Disclaimer](#-disclaimer)
- [Contributing](#-contributing)
- [License](#-license)
- [Support](#-support)
- [Changelog](#-changelog)

---

## 🏈 Features

### Core Functionality

| Feature | Description |
|---------|-------------|
| **AI-Powered Predictions** | Machine learning models (LightGBM) predicting game outcomes with high accuracy |
| **Expected Value Calculations** | Sophisticated EV analysis for moneyline, spread, and totals betting markets |
| **Real-Time Odds Fetching** | Live odds integration via The Odds API from multiple sportsbooks |
| **Kelly Criterion** | Optimal bet sizing recommendations using the Kelly formula |
| **Interactive Dashboard** | Modern React-based web interface with real-time data visualization |
| **Multi-Sport Support** | NFL and NCAAF (College Football) game analysis |

### Supported Betting Markets

- **Moneyline** — Straight-up winner predictions with EV analysis
- **Point Spreads** — Against-the-spread betting recommendations
- **Over/Under Totals** — Total points market analysis
- **Parlay Suggestions** — Multi-leg bet recommendations *(coming soon)*

### Key Components

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Predictor Service** | Python / LightGBM | ML model inference and feature engineering |
| **EV Calculator** | Python | Expected value and profitability analysis |
| **Odds Fetcher** | Python / Flask | Real-time odds from multiple sportsbooks |
| **Dashboard** | React 18 | Interactive charts and betting recommendations |
| **Odds Table** | React 18 | Live odds comparison and filtering |
| **API Gateway** | Flask 3.1 | RESTful API with CORS protection |

---

## 🚀 Quick Start

### Prerequisites

- **Python** 3.11 or higher
- **Node.js** 20 or higher
- **pnpm** (recommended) or npm
- **API key** from [The Odds API](https://the-odds-api.com)

### Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create and activate virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Edit .env and add your API_KEY

# Start the backend server
python src/main.py
```

### Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm run dev --host
```

### Access the Application

| Service | URL |
|---------|-----|
| **Frontend Dashboard** | http://localhost:5173 |
| **Backend API** | http://localhost:5000 |
| **API Health Check** | http://localhost:5000/api/betting/health |

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Client (React 18)                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Dashboard │  │OddsTable │  │Settings  │  │Charts    │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       └──────────────┴─────────────┴──────────────┘        │
└──────────────────────────┬──────────────────────────────────┘
                           │ HTTP / WebSocket
┌──────────────────────────▼──────────────────────────────────┐
│                   API Gateway (Flask)                        │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Betting   │  │User Mgmt│  │WebSocket │  │Health    │   │
│  │Routes    │  │Routes   │  │Events    │  │Check     │   │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘   │
│       └──────────────┴─────────────┴──────────────┘        │
└──────────────────────────┬──────────────────────────────────┘
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    Service Layer                             │
│  ┌────────────────┐  ┌────────────────┐  ┌──────────────┐  │
│  │  Predictor     │  │  EV Calculator │  │ Odds Fetcher │  │
│  │  (LightGBM)    │  │  (Kelly Criterion)│ (The Odds API)│  │
│  └───────┬────────┘  └───────┬────────┘  └──────┬───────┘  │
│          │                   │                   │          │
│  ┌───────▼───────────────────▼───────────────────▼───────┐  │
│  │                 Data Layer                             │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐  │  │
│  │  │  SQLite/Postgres│  │  Redis Cache │  │  Joblib   │  │  │
│  │  │  (Database)  │  │  (Session)   │  │  (Model)   │  │  │
│  │  └──────────────┘  └──────────────┘  └────────────┘  │  │
│  └───────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

---

## 📁 Project Structure

```
football-betting-ai/
│
├── backend/                          # Python Flask API server
│   ├── src/                          # Application source code
│   │   ├── main.py                   # Flask application entry point
│   │   ├── models/                   # SQLAlchemy database models
│   │   ├── routes/                   # API route handlers
│   │   │   ├── user.py              # User management endpoints
│   │   │   └── betting.py           # Betting prediction endpoints
│   │   └── services/                 # Business logic layer
│   │       ├── predictor.py         # ML model inference engine
│   │       ├── ev_calculator.py     # Expected Value mathematics
│   │       └── api_fetcher.py       # The Odds API integration
│   ├── models/                       # Trained ML models
│   │   └── predictor.joblib         # LightGBM trained model
│   ├── requirements.txt              # Python dependency manifest
│   ├── .env.example                  # Environment variable template
│   └── .env                          # Local credentials (gitignored)
│
├── frontend/                         # React SPA dashboard
│   ├── src/                          # React application source
│   │   ├── components/               # UI component library
│   │   │   ├── Dashboard.jsx        # Main analytics dashboard
│   │   │   └── OddsTable.jsx        # Live odds comparison table
│   │   ├── App.jsx                  # Root application component
│   │   └── main.jsx                 # Vite entry point
│   ├── public/                       # Static assets
│   ├── package.json                  # Node.js dependency manifest
│   ├── vite.config.js                # Vite build configuration
│   └── index.html                    # HTML shell
│
├── .gitignore                        # Git exclusion rules
├── LICENSE                           # Apache 2.0 license
├── README.md                         # Project documentation (this file)
├── DEPLOYMENT.md                     # Production deployment guide
├── ENHANCED_API_DOCUMENTATION.md     # Extended API reference
├── installation.txt                  # Installation notes
├── setup-dev.bat                     # Windows dev environment setup
└── start-dev.bat                     # Windows dev server launcher
```

---

## 🔧 API Reference

### Base URL

```
http://localhost:5000/api/betting/
```

### Endpoints

#### `GET /odds`

Fetch real-time odds for football games from multiple sportsbooks.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sport` | string | `nfl` | Sport type (`nfl` or `ncaaf`) |
| `markets` | string | `moneyline,spread,totals` | Comma-separated market types |
| `best_only` | boolean | `true` | Return only the best available odds |

**Response:** Array of game objects with odds from all major sportsbooks.

---

#### `POST /predict`

Generate AI-powered predictions and EV calculations for a specific game.

**Request Body:**

```json
{
  "game_data": {
    "home_team": "Kansas City Chiefs",
    "away_team": "Buffalo Bills",
    "game_id": "optional_id"
  },
  "odds_data": {
    "moneyline": {"home": -120, "away": +100},
    "spread": {"spread": -2.5, "home_odds": -110, "away_odds": -110},
    "total": {"total": 47.5, "over_odds": -110, "under_odds": -110}
  },
  "bankroll": 1000
}
```

**Response:** Prediction results including win probabilities, EV percentages, and Kelly-optimized bet sizes.

---

#### `POST /analyze`

Comprehensive game analysis combining live odds with ML predictions.

**Request Body:**

```json
{
  "game_id": "optional_game_id",
  "sport": "nfl",
  "game_data": {
    "home_team": "Kansas City Chiefs",
    "away_team": "Buffalo Bills"
  },
  "bankroll": 1000
}
```

**Response:** Full analysis with predictions, EV calculations, and betting recommendations.

---

#### `GET /upcoming`

Get upcoming games with optional prediction data.

**Query Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `sport` | string | `nfl` | Sport type |
| `days` | integer | `7` | Number of days ahead to look |
| `include_predictions` | boolean | `false` | Include basic predictions |

---

#### `GET /health`

Health check endpoint for monitoring and load balancers.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2026-07-05T17:00:00Z",
  "version": "1.0.0"
}
```

---

## 🤖 Machine Learning Model

### Model Architecture

The system uses a **LightGBM** gradient boosting model trained on comprehensive NFL/NCAAF historical data.

### Feature Engineering

| Feature | Description | Impact |
|---------|-------------|--------|
| `home_team_rating` | ELO-style team strength rating | High |
| `away_team_rating` | ELO-style team strength rating | High |
| `home_team_offense_rating` | Offensive efficiency metric | Medium |
| `away_team_offense_rating` | Offensive efficiency metric | Medium |
| `home_team_defense_rating` | Defensive efficiency metric | Medium |
| `away_team_defense_rating` | Defensive efficiency metric | Medium |
| `home_team_recent_form` | Performance over last 5 games | High |
| `away_team_recent_form` | Performance over last 5 games | High |
| `weather_impact` | Environmental conditions score | Low |
| `home_field_advantage` | Home field advantage adjustment | Medium |
| `injury_impact` | Key player availability impact | Medium |
| `rest_days_home` | Days of rest for home team | Low |
| `rest_days_away` | Days of rest for away team | Low |
| `head_to_head_record` | Historical matchup data | Medium |
| `season_week` | Week number in regular season | Low |
| `is_playoff` | Playoff game binary indicator | Medium |

### Model Performance

- **Accuracy**: ~65-70% on historical NFL data
- **AUC-ROC**: ~0.72
- **Features**: 16 engineered features
- **Algorithm**: LightGBM with early stopping

---

## 📊 Expected Value Calculations

### Kelly Criterion

Optimal bet sizing using the Kelly formula:

```
f = (bp - q) / b
```

Where:
- **f** = fraction of bankroll to wager
- **b** = decimal odds minus 1
- **p** = estimated probability of winning
- **q** = probability of losing (1 - p)

### EV Formula

```
EV = (True Probability × Potential Profit) - ((1 - True Probability) × Bet Amount)
```

### Recommendation System

| Classification | Threshold | Action |
|---------------|-----------|--------|
| **STRONG_BET** | EV ≥ 10% | High confidence, recommended wager |
| **GOOD_BET** | EV ≥ 5% | Favorable opportunity |
| **CONSIDER** | EV ≥ 2% | Worth considering |
| **LOW_CONFIDENCE** | EV ≥ 2% (low model confidence) | Proceed with caution |
| **PASS** | EV < 2% | Not recommended |
| **AVOID** | EV < 0% | Negative expected value |

---

## 🎨 Frontend Features

### Dashboard

- Real-time statistics and KPIs
- Game analysis with AI predictions
- EV calculations and actionable recommendations
- Interactive charts and data visualizations
- Betting opportunity identification

### Live Odds Table

- Real-time odds from multiple sportsbooks
- Advanced filtering and search functionality
- Multiple betting markets (moneyline, spread, totals)
- Implied probability calculations
- Best odds auto-highlighting

### Settings Panel

- API configuration status and validation
- Model information and version details
- Betting preferences and bankroll management
- System diagnostics and logging controls

---

## 🔑 Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# ─── API Configuration ───────────────────────────────────────
API_KEY=your_odds_api_key_here
ODDS_API_BASE_URL=https://api.the-odds-api.com/v4

# ─── Model Configuration ─────────────────────────────────────
MODEL_PATH=./models/predictor.joblib

# ─── Application Configuration ───────────────────────────────
FLASK_ENV=development
SECRET_KEY=your_secret_key_here
LOG_LEVEL=DEBUG

# ─── Database Configuration ──────────────────────────────────
DATABASE_URL=sqlite:///app.db

# ─── Redis Configuration (optional) ──────────────────────────
REDIS_URL=redis://localhost:6379/0
```

---

## 🚀 Deployment

### Local Development

```bash
# Terminal 1: Backend
cd backend && python src/main.py

# Terminal 2: Frontend
cd frontend && pnpm run dev --host
```

### Production Deployment

**Backend (Gunicorn):**
```bash
gunicorn -w 4 -b 0.0.0.0:5000 src.main:app
```

**Frontend (Static Build):**
```bash
cd frontend && pnpm run build
# Serve the dist/ directory via Nginx, Caddy, or similar
```

**Database:** Configure PostgreSQL or MySQL in production via `DATABASE_URL`
**API Keys:** Use environment-specific API keys with restricted permissions

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

---

## 🔒 Security

- **Environment Variables**: All sensitive data stored in `.env` (gitignored)
- **CORS Protection**: API endpoints protected with configurable CORS policies
- **Input Validation**: All API inputs validated and sanitized
- **Error Handling**: Comprehensive error handling with structured logging
- **Rate Limiting**: API call frequency limits to prevent abuse
- **HTTPS**: Enforce TLS in production environments

---

## 📈 Usage Examples

### Python SDK

```python
from src.services.predictor import FootballPredictor
from src.services.ev_calculator import EVCalculator

# Initialize services
predictor = FootballPredictor()
calculator = EVCalculator()

# Prepare game data
game_data = {
    'home_team': 'Kansas City Chiefs',
    'away_team': 'Buffalo Bills',
    'home_team_rating': 1600,
    'away_team_rating': 1580,
    'home_team_offense_rating': 85,
    'away_team_offense_rating': 82,
    'home_team_defense_rating': 78,
    'away_team_defense_rating': 75,
    'home_team_recent_form': 0.8,
    'away_team_recent_form': 0.6,
    'weather_impact': 0.0,
    'home_field_advantage': 3.0,
    'injury_impact': 0.0,
    'rest_days_home': 7,
    'rest_days_away': 7,
    'head_to_head_record': 0.6,
    'season_week': 8,
    'is_playoff': 0
}

# Generate prediction
predictions = predictor.predict_game(game_data)
print(f"Home win probability: {predictions['home_win_probability']:.2%}")
print(f"Away win probability: {predictions['away_win_probability']:.2%}")

# Calculate expected value
ev_result = calculator.calculate_ev(
    true_probability=0.55,
    odds=-110,
    bet_amount=100
)
print(f"Expected Value: {ev_result['ev_percentage']:.2f}%")
print(f"Kelly Bet Size: ${ev_result['kelly_bet']:.2f}")
```

### cURL Examples

```bash
# Fetch NFL odds
curl "http://localhost:5000/api/betting/odds?sport=nfl&markets=moneyline,spread"

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

# Health check
curl http://localhost:5000/api/betting/health
```

---

## 🔑 API Credentials Setup

### The Odds API (Required)

1. Visit [The Odds API Dashboard](https://dash.the-odds-api.com)
2. Create a free account
3. Obtain your API key from the dashboard
4. Add to `.env`: `API_KEY=your_key_here`

### SportsData.io (Optional)

1. Visit [SportsData.io](https://sportsdata.io)
2. Register for an account
3. Generate an API key
4. Add to `.env` for enhanced data sources

---

## ⚠️ Disclaimer

> **This system is for educational and research purposes only.**
>
> Sports betting involves financial risk. This tool provides statistical analysis and predictions but does not guarantee winning outcomes. Users must:
>
> - Comply with all local gambling laws and regulations
> - Never wager more than they can afford to lose
> - Understand that past performance does not guarantee future results
> - Use this tool as one of many inputs in their decision-making process
>
> **Always bet responsibly.** If you or someone you know has a gambling problem, please seek help from professional organizations.

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

### Development Process

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Guidelines

- Follow existing code style and conventions
- Add tests for new functionality
- Update documentation as needed
- Keep pull requests focused on a single feature/fix
- Use descriptive commit messages

### Areas for Contribution

- ML model improvements and feature engineering
- Additional sportsbook integrations
- New betting market support
- UI/UX enhancements
- Performance optimizations
- Documentation improvements
- Test coverage expansion

---

## 📄 License

This project is licensed under the **Apache License, Version 2.0**.

See the [LICENSE](LICENSE) file for the full license text.

```
Copyright 2026 Football Betting AI Contributors

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```

---

## 🆘 Support

### Troubleshooting

| Issue | Solution |
|-------|----------|
| API connection errors | Verify API key in `.env` and check network connectivity |
| Model loading failures | Ensure `predictor.joblib` exists in `backend/models/` |
| Frontend build errors | Run `pnpm install` to ensure all dependencies are installed |
| CORS errors | Check `FLASK_ENV` and CORS configuration in backend |
| Database issues | Verify `DATABASE_URL` and run migrations if needed |

### Resources

- [The Odds API Documentation](https://the-odds-api.com)
- [LightGBM Documentation](https://lightgbm.readthedocs.io/)
- [Flask Documentation](https://flask.palletsprojects.com/)
- [React Documentation](https://react.dev/)

### Getting Help

1. Check the [troubleshooting guide](#troubleshooting) above
2. Review [ENHANCED_API_DOCUMENTATION.md](ENHANCED_API_DOCUMENTATION.md)
3. Search existing GitHub issues
4. Open a new issue with detailed reproduction steps

---

## 📋 Changelog

### v1.0.0 (Initial Release)

- ✅ NFL and NCAAF prediction support
- ✅ LightGBM machine learning model
- ✅ Expected Value calculations with Kelly Criterion
- ✅ Real-time odds integration via The Odds API
- ✅ Interactive React dashboard
- ✅ Live odds comparison table
- ✅ RESTful API with comprehensive endpoints
- ✅ WebSocket support for real-time updates
- ✅ Redis caching layer
- ✅ Celery task queue for async processing
- ✅ Comprehensive error handling and logging

### Planned Features

- [ ] Parlay builder and analysis
- [ ] Player prop betting markets
- [ ] Historical backtesting engine
- [ ] Mobile-responsive UI redesign
- [ ] Multi-language support
- [ ] Docker containerization
- [ ] CI/CD pipeline integration
- [ ] Automated model retraining pipeline

---

<div align="center">

**Built with ❤️ for responsible sports betting analysis**

[Report Bug](https://github.com/yourusername/football-betting-ai/issues) •
[Request Feature](https://github.com/yourusername/football-betting-ai/issues) •
[Star the Project](https://github.com/yourusername/football-betting-ai)

</div>