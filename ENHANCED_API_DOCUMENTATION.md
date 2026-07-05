# Enhanced Football Betting AI - Advanced API Documentation

## 🚀 New Enhanced Endpoints

Your football betting AI system has been upgraded with sophisticated edge calculation capabilities and ChatGPT integration as requested by your client. Here's the complete documentation for the new advanced features.

## 📊 Advanced EV Calculator Features

### Key Enhancements Implemented:

1. **Sophisticated EV Formulas**: Exact implementation of client's requested formulas
2. **Live Betting Projections**: Real-time total projections with EPA integration
3. **ChatGPT AI Analysis**: Intelligent reasoning for betting opportunities
4. **No-Vig Probability Calculations**: Remove bookmaker margins
5. **EPA-Based Models**: Expected Points Added statistical integration
6. **Real-Time Alerts**: Automated opportunity detection

## 🔧 New API Endpoints

### 1. Advanced Game Analysis
**POST** `/api/enhanced/advanced-analysis`

Performs sophisticated betting analysis with EPA-based models and AI insights.

**Request Body:**
```json
{
  "game_data": {
    "home_team": "Miami Dolphins",
    "away_team": "New England Patriots",
    "home_team_rating": 1580,
    "away_team_rating": 1520,
    "home_off_epa_per_play": 0.05,
    "away_off_epa_per_play": -0.02,
    "home_def_epa_per_play": -0.03,
    "away_def_epa_per_play": 0.01,
    "home_field_advantage": 3.0,
    "weather_impact": -1.5
  },
  "odds_data": {
    "moneyline": {"home": -150, "away": +130},
    "spread": {"spread": -3.5, "home_odds": -110, "away_odds": -110},
    "total": {"total": 47.5, "over_odds": -110, "under_odds": -110}
  },
  "include_ai_analysis": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "analysis": {
      "moneyline": {
        "home_win_prob": 0.65,
        "away_win_prob": 0.35,
        "home_ev": 0.083,
        "away_ev": -0.045,
        "home_ev_percentage": 8.3,
        "recommendation": "GOOD_BET"
      },
      "spread": {
        "projected_margin": 4.2,
        "prob_cover": 0.55,
        "ev": 0.05,
        "ev_percentage": 5.0,
        "recommendation": "GOOD_BET"
      },
      "total": {
        "projected_total": 45.8,
        "prob_over": 0.42,
        "prob_under": 0.58,
        "under_ev": 0.061,
        "under_ev_percentage": 6.1,
        "recommendation": "CONSIDER"
      },
      "summary": {
        "best_market": "moneyline",
        "best_ev": 0.083,
        "overall_recommendation": "GOOD_BET"
      }
    },
    "ai_insights": "Strong value on Miami ML at -150. EPA differential favors home team significantly. Weather impact minimal. Confidence: High due to 8.3% edge and favorable matchup metrics.",
    "calculation_method": "advanced_ev_with_epa"
  }
}
```

### 2. Live Edge Calculation
**POST** `/api/enhanced/live-edge-calculation`

Calculate betting edge for live games with real-time projections.

**Request Body:**
```json
{
  "game_state": {
    "game_id": "NE@MIA-2025-01-15",
    "home_team": "Miami Dolphins",
    "away_team": "New England Patriots",
    "home_score": 14,
    "away_score": 10,
    "quarter": 2,
    "clock": "8:30",
    "minutes_remaining": 38.5,
    "home_ppm_estimate": 0.68,
    "away_ppm_estimate": 0.61,
    "home_off_epa_per_play": 0.05,
    "away_off_epa_per_play": -0.02
  },
  "current_odds": {
    "total": {"total": 45.5, "over_odds": -105, "under_odds": -115},
    "spread": {"spread": -2.5, "home_odds": -110, "away_odds": -110}
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "live_analysis": {
      "total": {
        "projected_total": 48.2,
        "current_total": 24,
        "projected_additional_points": 24.2,
        "prob_over": 0.72,
        "over_ev": 0.191,
        "over_ev_percentage": 19.1,
        "recommendation": "STRONG_BET"
      }
    },
    "betting_alerts": [
      {
        "market": "total",
        "ev_percentage": 19.1,
        "recommendation": "STRONG_BET",
        "confidence": 0.64,
        "message": "🚨 LIVE TOTAL ALERT\nNE 10 - MIA 14 (Q2 8:30)\nProjected: 48.2 | Line: 45.5\nBet OVER - 19.1% EV"
      }
    ],
    "game_state_summary": {
      "current_score": "10-14",
      "time_remaining": 38.5,
      "quarter": 2
    }
  }
}
```

### 3. Implied Probability Calculator
**POST** `/api/enhanced/implied-probability`

Calculate implied probabilities and remove vig from odds.

**Request Body:**
```json
{
  "odds": {
    "over": -110,
    "under": -105
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "implied_probabilities": {
      "over": 0.5238,
      "under": 0.5122,
      "total": 1.036
    },
    "no_vig_probabilities": {
      "over": 0.5056,
      "under": 0.4944
    },
    "vig_percentage": 3.6,
    "decimal_odds": {
      "over": 1.909,
      "under": 1.952
    }
  }
}
```

### 4. Expected Value Calculator
**POST** `/api/enhanced/ev-calculator`

Calculate Expected Value for specific betting scenarios.

**Request Body:**
```json
{
  "your_probability": 0.61,
  "odds": -105,
  "bet_amount": 100
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "expected_value": 0.191,
    "ev_percentage": 19.1,
    "expected_profit": 19.10,
    "edge": 0.098,
    "edge_percentage": 9.8,
    "recommendation": "STRONG_BET",
    "bet_details": {
      "bet_amount": 100,
      "potential_profit": 95.24,
      "potential_loss": 100,
      "your_probability": 0.61,
      "implied_probability": 0.512,
      "decimal_odds": 1.952
    },
    "risk_assessment": {
      "win_probability": 0.61,
      "lose_probability": 0.39,
      "expected_return": 119.10
    }
  }
}
```

### 5. Live Game Simulation
**POST** `/api/enhanced/simulation/live-update`

Simulate live game updates for testing.

**Request Body:**
```json
{
  "game_id": "NE@MIA-2025-01-15",
  "score_update": {
    "home_score": 21,
    "away_score": 10,
    "quarter": 3,
    "minutes_remaining": 30.0
  }
}
```

## 📈 Advanced Calculation Formulas

### 1. Implied Probability
```
Negative odds: |odds| / (|odds| + 100)
Positive odds: 100 / (odds + 100)
```

### 2. No-Vig Probability
```
no_vig_prob = implied_prob / (sum_of_implied_probs)
vig = sum_of_implied_probs - 1
```

### 3. Expected Value
```
EV = (your_prob * (decimal_odds - 1)) - (1 - your_prob)
```

### 4. Live Total Projection
```
projected_total = current_points + (minutes_remaining * avg_ppm) + adjustments
adjustments = quarter_factor + epa_impact + situational_factors
```

### 5. Spread Edge Calculation
```
projected_margin = rating_diff + epa_diff + home_advantage
prob_cover = 1 - normal_cdf(0, margin_vs_spread, std_dev)
```

## 🤖 AI Analysis Integration

The system now includes ChatGPT-4 integration for intelligent analysis:

- **Contextual Insights**: AI analyzes statistical factors and provides reasoning
- **Risk Assessment**: Evaluates confidence levels and situational factors
- **Actionable Recommendations**: Clear, concise betting guidance
- **Factor Identification**: Highlights key drivers of betting edges

## 🚨 Real-Time Alert System

### Alert Thresholds:
- **STRONG_BET**: EV ≥ 10%
- **GOOD_BET**: EV ≥ 5%
- **CONSIDER**: EV ≥ 3%
- **SLIGHT_EDGE**: EV ≥ 1%
- **PASS**: EV < 1%
- **AVOID**: EV < 0%

### Alert Format:
```
🚨 LIVE TOTAL ALERT
NE 10 - MIA 14 (Q2 8:30)
Projected: 48.2 | Line: 45.5
Bet OVER - 19.1% EV
```

## 🔧 Configuration

### Environment Variables Added:
```env
OPENAI_API_KEY=your_chatgpt_api_key_here
```

### Dependencies Added:
```
openai==1.54.3
scipy==1.11.3
```

## 📊 Usage Examples

### Example 1: Advanced Pre-Game Analysis
```python
import requests

# Analyze game with EPA data
response = requests.post('http://localhost:5000/api/enhanced/advanced-analysis', json={
    "game_data": {
        "home_team": "Kansas City Chiefs",
        "away_team": "Buffalo Bills",
        "home_off_epa_per_play": 0.12,
        "away_off_epa_per_play": 0.08,
        "home_def_epa_per_play": -0.05,
        "away_def_epa_per_play": -0.03
    },
    "odds_data": {
        "total": {"total": 54.5, "over_odds": -110, "under_odds": -110}
    },
    "include_ai_analysis": true
})

result = response.json()
print(f"Best EV: {result['data']['analysis']['summary']['best_ev']:.3f}")
print(f"AI Insight: {result['data']['ai_insights']}")
```

### Example 2: Live Betting Edge
```python
# Calculate live edge during game
response = requests.post('http://localhost:5000/api/enhanced/live-edge-calculation', json={
    "game_state": {
        "game_id": "KC@BUF-2025-01-15",
        "home_score": 28,
        "away_score": 21,
        "quarter": 4,
        "minutes_remaining": 8.5,
        "home_ppm_estimate": 0.72,
        "away_ppm_estimate": 0.68
    },
    "current_odds": {
        "total": {"total": 52.5, "over_odds": -105, "under_odds": -115}
    }
})

alerts = response.json()['data']['betting_alerts']
for alert in alerts:
    if alert['ev_percentage'] > 5:
        print(f"ALERT: {alert['message']}")
```

## 🎯 Key Features Summary

✅ **Advanced EV Calculations** - Sophisticated formulas with EPA integration  
✅ **Live Betting Engine** - Real-time projections and alerts  
✅ **ChatGPT Integration** - AI-powered analysis and insights  
✅ **No-Vig Calculations** - Remove bookmaker margins  
✅ **EPA Statistical Models** - Expected Points Added integration  
✅ **Real-Time Monitoring** - Automated opportunity detection  
✅ **Comprehensive API** - 8+ new endpoints for advanced analysis  

## 📞 Support

The enhanced system maintains backward compatibility with existing endpoints while adding powerful new capabilities for sophisticated betting analysis.

For questions about the enhanced features, refer to the comprehensive error handling and logging built into each endpoint.
