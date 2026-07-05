# Frontend — Football Betting AI Dashboard

<div align="center">

[![React](https://img.shields.io/badge/React-19%2B-61DAFB)](https://reactjs.org/)
[![Vite](https://img.shields.io/badge/Build-Vite-646CFF)](https://vitejs.dev/)
[![Tailwind CSS](https://img.shields.io/badge/Styles-Tailwind%204-06B6D4)](https://tailwindcss.com/)
[![shadcn/ui](https://img.shields.io/badge/UI-shadcn%2Fui-000000)](https://ui.shadcn.com/)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue)](../LICENSE)

**Modern React-based dashboard for the Football Betting AI Prediction System — featuring real-time odds visualization, ML-powered predictions, interactive charts, and ESPN-style scoreboards.**

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Tech Stack](#-tech-stack)
- [Project Structure](#-project-structure)
- [Components](#-components)
- [Features](#-features)
- [Installation](#-installation)
- [Development](#-development)
- [Build & Deployment](#-build--deployment)
- [API Integration](#-api-integration)
- [UI Library](#-ui-library)
- [Contributing](#-contributing)
- [License](#-license)

---

## 🎯 Overview

The frontend is a **React 19 single-page application** built with **Vite** and styled with **Tailwind CSS 4** using **shadcn/ui** components. It provides an interactive, real-time dashboard for analyzing football betting data.

### Key Capabilities

| Capability | Description |
|------------|-------------|
| **Interactive Dashboard** | Real-time KPIs, charts, and betting insights |
| **Live Odds Comparison** | Side-by-side odds from multiple sportsbooks |
| **ML Prediction Display** | AI-powered win probability visualization |
| **ESPN-Style Scoreboard** | Live scores and game status for NFL & NCAAF |
| **Real-Time Updates** | WebSocket-powered live data streaming |
| **Betting Opportunities** | Auto-detected positive EV betting spots |
| **Responsive Design** | Works on desktop, tablet, and mobile |

---

## 🛠 Tech Stack

| Technology | Version | Purpose |
|------------|---------|---------|
| **React** | 19.1.0 | UI framework |
| **Vite** | 6.3.5 | Build tool and dev server |
| **Tailwind CSS** | 4.1.7 | Utility-first CSS framework |
| **shadcn/ui** | latest | Accessible UI component library |
| **Recharts** | 2.15.3 | Interactive charting library |
| **Framer Motion** | 12.15.0 | Animation library |
| **Lucide React** | 0.510.0 | Icon library |
| **React Router** | 7.6.1 | Client-side routing |
| **Socket.IO Client** | 4.7.5 | WebSocket real-time communication |
| **date-fns** | 4.1.0 | Date utility library |
| **Radix UI** | latest | Headless UI primitives |
| **Zod** | 3.24.4 | Schema validation |
| **React Hook Form** | 7.56.3 | Form management |

---

## 📁 Project Structure

```
frontend/
│
├── public/                           # Static assets
│   └── favicon.ico                   # Browser tab icon
│
├── src/                              # Application source code
│   ├── components/                   # React component library
│   │   ├── Dashboard.jsx            # Main analytics dashboard
│   │   ├── OddsTable.jsx            # Live odds comparison table
│   │   ├── UpcomingMatches.jsx      # Upcoming games with predictions
│   │   ├── LiveMatches.jsx          # Live in-play games view
│   │   ├── LiveOpportunities.jsx    # Real-time betting opportunities
│   │   ├── ESPNScoreboard.jsx       # ESPN-style scoreboard display
│   │   └── ui/                      # shadcn/ui components (30+)
│   │       ├── accordion.jsx        # Expandable accordion
│   │       ├── alert-dialog.jsx     # Confirmation dialogs
│   │       ├── alert.jsx            # Alert banners
│   │       ├── badge.jsx            # Status badges
│   │       ├── button.jsx           # Button primitives
│   │       ├── card.jsx             # Card containers
│   │       ├── chart.jsx            # Chart components
│   │       ├── dialog.jsx           # Modal dialogs
│   │       ├── dropdown-menu.jsx    # Dropdown menus
│   │       ├── form.jsx             # Form components
│   │       ├── input.jsx            # Input fields
│   │       ├── select.jsx           # Select dropdowns
│   │       ├── table.jsx            # Data tables
│   │       ├── tabs.jsx             # Tab navigation
│   │       ├── tooltip.jsx          # Tooltips
│   │       └── ... (20+ more)       # Additional components
│   │
│   ├── hooks/                       # Custom React hooks
│   │   ├── useSocket.js             # WebSocket connection hook
│   │   └── use-mobile.js            # Responsive detection hook
│   │
│   ├── lib/                         # Utility libraries
│   │   ├── api.js                   # API client and endpoint definitions
│   │   └── utils.js                 # General utility functions
│   │
│   ├── services/                    # External service integrations
│   │   └── socketService.js         # Socket.IO service layer
│   │
│   ├── App.jsx                      # Root application component
│   ├── App.css                      # Global styles
│   ├── index.css                    # Tailwind entry point
│   └── main.jsx                     # Vite entry point
│
├── index.html                       # HTML entry point
├── vite.config.js                   # Vite build configuration
├── package.json                     # Node.js dependencies
├── pnpm-lock.yaml                   # Lockfile (pnpm)
├── jsconfig.json                    # JavaScript config
├── eslint.config.js                 # ESLint configuration
├── components.json                  # shadcn/ui configuration
└── README.md                        # This file
```

---

## 🧩 Components

### Dashboard (`Dashboard.jsx`)

The central analytics hub displaying:

- **Key Performance Indicators** — Win rates, ROI, average EV
- **Upcoming Games Preview** — Next 5 games with quick predictions
- **EV Distribution Chart** — Recharts bar chart of expected value by market
- **Quick Stats** — Total opportunities, strong bets, bankroll impact
- **Data Refresh Controls** — Manual refresh button with loading state

### Odds Table (`OddsTable.jsx`)

Comprehensive odds comparison across sportsbooks:

- Multi-market display (moneyline, spread, totals)
- Best odds highlighting with color coding
- Implied probability calculations
- Sportsbook logo and name display
- Search and filter functionality
- Responsive table layout

### ESPN Scoreboard (`ESPNScoreboard.jsx`)

ESPN-style game scoreboard featuring:

- Live scores for NFL and NCAAF games
- Game status indicators (Scheduled, Live, Final)
- Team logos and records display
- Quarter-by-quarter scoring breakdown
- Game time and network information
- Tab-based switching between NFL and NCAAF

### Upcoming Matches (`UpcomingMatches.jsx`)

Upcoming games view with predictions:

- Game cards with team matchups
- AI prediction confidence indicators
- Win probability bars (visual)
- Game time and date display
- Sport type badges (NFL / NCAAF)

### Live Matches (`LiveMatches.jsx`)

Real-time in-play game tracking:

- Live game status updates
- Current score display
- In-play betting opportunities
- Auto-refresh capability

### Live Opportunities (`LiveOpportunities.jsx`)

Real-time betting opportunity detection:

- Positive EV opportunity cards
- Recommended bet display
- Kelly-optimized stake suggestions
- Opportunity expiration tracking

---

## 🚀 Installation

### Prerequisites

- **Node.js** 20 or higher
- **pnpm** 10+ (recommended) or npm

### Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
pnpm install

# Start development server
pnpm run dev --host
```

The frontend will be available at **http://localhost:5173**.

---

## 💻 Development

### Dev Server

```bash
pnpm run dev --host
# Available at http://localhost:5173
# Backend proxy at http://localhost:5000
```

The Vite dev server is configured to proxy `/api` requests to the Flask backend at `http://localhost:5000`, eliminating CORS issues during development.

### Available Scripts

| Script | Command | Description |
|--------|---------|-------------|
| `dev` | `vite` | Start development server |
| `build` | `vite build` | Production build |
| `preview` | `vite preview` | Preview production build |
| `lint` | `eslint .` | Run ESLint |

### Key Features

#### Real-Time Data Flow

```javascript
// Using the Socket.IO service
import { socketService } from '@/services/socketService';

// Connect to backend WebSocket
socketService.connect('http://localhost:5000');

// Listen for live odds updates
socketService.onOddsUpdate((data) => {
  console.log('New odds received:', data);
});

// Listen for game updates
socketService.onGameUpdate((data) => {
  console.log('Game updated:', data);
});
```

#### API Integration

```javascript
import { api } from '@/lib/api';

// Fetch odds
const odds = await api.getOdds({ sport: 'nfl', best_only: 'true' });

// Get predictions
const prediction = await api.predictGame({
  game_data: { home_team: 'Chiefs', away_team: 'Bills' },
  odds_data: { moneyline: { home: -120, away: +100 } },
  bankroll: 1000
});

// Get ESPN scoreboard
const scoreboard = await api.espn.getScoreboard({ days: 10 });
```

---

## 🏗 Build & Deployment

### Production Build

```bash
pnpm run build
# Output: dist/ directory with optimized static files
```

### Deployment Options

#### Option 1: Static File Server

```bash
# Build the frontend
pnpm run build

# Serve with any static file server (Nginx, Caddy, etc.)
# Example with Nginx:
server {
    listen 80;
    server_name your-domain.com;
    root /path/to/frontend/dist;
    
    location /api {
        proxy_pass http://backend:5000;
    }
    
    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

#### Option 2: Integrated with Backend

The Flask backend can serve the built frontend files:

1. Build frontend: `pnpm run build`
2. Copy `dist/` contents to `backend/src/static/`
3. Start the backend — it serves both API and frontend

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `VITE_API_URL` | `http://localhost:5000` | Backend API URL (production only) |

---

## 🔌 API Integration

### API Client (`src/lib/api.js`)

The API client provides a comprehensive interface for all backend endpoints:

```javascript
// ─── Betting Endpoints ──────────────────────────────────────
api.getOdds(params)           // Fetch live odds
api.predictGame(data)         // Generate predictions
api.analyzeGame(data)         // Comprehensive analysis
api.getUpcomingGames(params)  // Upcoming games

// ─── ESPN Endpoints ─────────────────────────────────────────
api.espn.getScoreboard(params)    // Full scoreboard (NFL + NCAAF)
api.espn.getLiveGames(params)     // Live games only
api.espn.getUpcomingGames(params) // Upcoming games
api.espn.getNFLGames(params)      // NFL only
api.espn.getNCAFGames(params)     // NCAAF only

// ─── Utility ────────────────────────────────────────────────
api.health()                  // Backend health check
```

---

## 🎨 UI Library

The frontend uses **shadcn/ui** — a collection of re-usable components built on **Radix UI** primitives and styled with **Tailwind CSS**.

### Installed Components (30+)

| Component | Usage |
|-----------|-------|
| **Tabs** | Main navigation between dashboard views |
| **Card** | Content containers for KPIs and data |
| **Badge** | Status indicators and counts |
| **Table** | Odds comparison data display |
| **Button** | Action triggers throughout |
| **Dialog** | Modal dialogs and overlays |
| **Dropdown Menu** | Context menus and filters |
| **Chart** | EV distribution and analytics |
| **Select** | Sport and market filters |
| **Accordion** | Collapsible content sections |
| **Alert** | Error and notification displays |
| **Tooltip** | Hover information |
| **Form** | Input forms and validation |
| **Scroll Area** | Scrollable content containers |

### Customization

All shadcn/ui components are copied directly into the source tree (`src/components/ui/`) for full customization. Modify them to match your branding and requirements.

---

## 📱 Responsive Design

The dashboard is fully responsive across device sizes:

| Breakpoint | Target | Layout |
|------------|--------|--------|
| **< 640px** | Mobile | Single column, stacked cards |
| **640-1024px** | Tablet | Two column grid |
| **> 1024px** | Desktop | Full multi-column layout |

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run `pnpm run lint` to check for issues
5. Commit and push
6. Open a Pull Request

### Areas for Contribution

- Additional dashboard widgets and visualizations
- Mobile responsiveness improvements
- Dark mode theme support
- Accessibility enhancements
- Performance optimizations
- New component development
- Unit and integration tests

---

## 📄 License

This project is licensed under the **Apache License, Version 2.0**. See the [LICENSE](../LICENSE) file for details.

---

<div align="center">
  <sub>Built with ❤️ for responsible sports betting analysis</sub>
  <br>
  <sub>Frontend Dashboard v1.0.0</sub>
</div>