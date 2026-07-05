import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign, 
  Target, 
  Activity,
  RefreshCw,
  AlertTriangle,
  CheckCircle
} from 'lucide-react';
import { ChevronRight } from 'lucide-react';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line
} from 'recharts';

const Dashboard = ({ upcomingGames, onRefresh, isLoading }) => {
  const [selectedGame, setSelectedGame] = useState(null);
  const [predictions, setPredictions] = useState(null);
  const [evCalculations, setEvCalculations] = useState(null);
  const [bettingSummary, setBettingSummary] = useState(null);
  const [analyzing, setAnalyzing] = useState(false);

  // Debug log to check incoming data
  console.log('Dashboard received upcomingGames:', upcomingGames?.length || 0);
  if (upcomingGames?.length > 0) {
    const nflCount = upcomingGames.filter(g => g.sport_key === 'americanfootball_nfl').length;
    const ncaafCount = upcomingGames.filter(g => g.sport_key === 'americanfootball_ncaaf').length;
    console.log('Dashboard game breakdown - NFL:', nflCount, 'NCAAF:', ncaafCount);
    console.log('First 20 games sport_key check:', upcomingGames.slice(0, 20).map((g, i) => ({ 
      index: i,
      teams: `${g.away_team} @ ${g.home_team}`, 
      sport_key: g.sport_key 
    })));
  }

  const formatGameTime = (timeString) => {
    if (!timeString) return 'TBD';
    
    try {
      const date = new Date(timeString);
      return date.toLocaleDateString('en-US', {
        month: 'numeric',
        day: 'numeric',
        year: 'numeric',
        hour: 'numeric',
        minute: '2-digit',
        hour12: true
      });
    } catch (error) {
      return timeString;
    }
  };

  const getGameStatus = (gameTime) => {
    if (!gameTime) return { status: 'upcoming', label: 'Upcoming', color: 'bg-blue-100 text-blue-800' };
    
    const now = new Date();
    const gameDate = new Date(gameTime);
    const timeDiff = gameDate.getTime() - now.getTime();
    const hoursDiff = timeDiff / (1000 * 60 * 60);
    
    // Game is live if it started within the last 4 hours and hasn't been more than 4 hours
    if (hoursDiff <= 0 && hoursDiff >= -4) {
      return { status: 'live', label: 'Live', color: 'bg-red-100 text-red-800' };
    }
    // Game is completed if it started more than 4 hours ago
    else if (hoursDiff < -4) {
      return { status: 'completed', label: 'Final', color: 'bg-gray-100 text-gray-800' };
    }
    // Game is upcoming
    else {
      return { status: 'upcoming', label: 'Upcoming', color: 'bg-blue-100 text-blue-800' };
    }
  };

  // Calculate dashboard statistics
  const calculateStats = () => {
    if (!upcomingGames || upcomingGames.length === 0) {
      return {
        totalGames: 0,
        profitableOpportunities: 0,
        averageConfidence: 0,
        bestOpportunity: 'None'
      };
    }

    // Show all upcoming games (no date filtering)
    const recentGames = upcomingGames;

    const gamesWithPredictions = recentGames.filter(game => 
      game.predictions && 
      game.predictions.confidence_score && 
      !isNaN(game.predictions.confidence_score)
    );
    
    const profitableGames = gamesWithPredictions.filter(game => {
      const confidence = game.predictions.confidence_score;
      return confidence > 0.65; // 65% confidence threshold
    });

    const averageConfidence = gamesWithPredictions.length > 0 ? 
      gamesWithPredictions.reduce((sum, game) => sum + (game.predictions.confidence_score || 0), 0) / gamesWithPredictions.length : 0;

    const bestGame = gamesWithPredictions.length > 0 ? 
      gamesWithPredictions.reduce((best, game) => 
        (game.predictions.confidence_score > (best.predictions?.confidence_score || 0)) ? game : best
      ) : null;

    return {
      totalGames: upcomingGames.length, // Show total upcoming games, not just filtered ones
      recentGames: recentGames.length, // Games within next 10 days
      profitableOpportunities: profitableGames.length,
      averageConfidence: (averageConfidence * 100).toFixed(1),
      bestOpportunity: bestGame ? `${bestGame.away_team} @ ${bestGame.home_team}` : 'None'
    };
  };

  const stats = calculateStats();

  const analyzeGame = async (game) => {
    setAnalyzing(true);
    setSelectedGame(game);
    
    try {
      const gameData = {
        home_team: game.home_team,
        away_team: game.away_team,
        game_id: game.id
      };

      console.log('Making API request to:', '/api/betting/analyze');
      console.log('Request data:', { game_data: gameData, sport: 'nfl', bankroll: 1000 });
      
      const response = await fetch('/api/betting/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          game_data: gameData,
          sport: game.sport_key === 'americanfootball_ncaaf' ? 'ncaaf' : 'nfl',
          bankroll: 1000
        })
      });
      
      console.log('Response received:', {
        status: response.status,
        statusText: response.statusText,
        contentType: response.headers.get('content-type'),
        url: response.url
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error('API Error Details:', {
          status: response.status,
          statusText: response.statusText,
          contentType: response.headers.get('content-type'),
          url: response.url,
          errorText: errorText.substring(0, 200)
        });
        throw new Error(`API Error ${response.status}: ${errorText.substring(0, 100)}`);
      }

      const result = await response.json();
      
      if (result.success) {
        setPredictions(result.data.predictions);
        setEvCalculations(result.data.ev_calculations);
        setBettingSummary(result.data.betting_summary);
      } else {
        console.error('Analysis failed:', result.error);
      }
    } catch (error) {
      console.error('Error analyzing game:', error);
    } finally {
      setAnalyzing(false);
    }
  };

  const getRecommendationColor = (recommendation) => {
    switch (recommendation) {
      case 'STRONG_BET': return 'bg-green-500';
      case 'GOOD_BET': return 'bg-blue-500';
      case 'CONSIDER': return 'bg-yellow-500';
      case 'LOW_CONFIDENCE': return 'bg-orange-500';
      case 'PASS': return 'bg-gray-500';
      case 'AVOID': return 'bg-red-500';
      default: return 'bg-gray-500';
    }
  };

  const formatCurrency = (amount) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD'
    }).format(amount);
  };

  const formatOdds = (odds) => {
    if (!odds) return 'N/A';
    return odds > 0 ? `+${odds}` : `${odds}`;
  };

  // Prepare chart data for EV visualization
  const prepareEVChartData = () => {
    if (!evCalculations) return [];
    
    return Object.entries(evCalculations).map(([market, data]) => ({
      market: market.replace('_', ' ').toUpperCase(),
      ev: data.ev_percentage,
      recommendation: data.recommendation
    }));
  };

  const prepareProbabilityData = () => {
    if (!predictions) return [];
    
    return [
      { name: 'Home Win', value: predictions.home_win_probability * 100, color: '#8884d8' },
      { name: 'Away Win', value: predictions.away_win_probability * 100, color: '#82ca9d' }
    ];
  };

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold">Football Betting Dashboard</h1>
          <p className="text-muted-foreground">AI-powered betting predictions and EV analysis</p>
        </div>
        <Button onClick={onRefresh} disabled={isLoading} className="flex items-center gap-2">
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Data
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Total Games</CardTitle>
            <Activity className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.totalGames}</div>
            <p className="text-xs text-muted-foreground">
              All upcoming games
            </p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Profitable Opportunities</CardTitle>
            <Target className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.profitableOpportunities}</div>
            <p className="text-xs text-muted-foreground">High confidence bets</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Average Confidence</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.averageConfidence || 0}%</div>
            <p className="text-xs text-muted-foreground">Across all games</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">Best Opportunity</CardTitle>
            <DollarSign className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.bestOpportunity || 'None'}</div>
            <p className="text-xs text-muted-foreground">Best matchup</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Upcoming Games List */}
        <Card>
          <CardHeader>
            <CardTitle>Upcoming Games</CardTitle>
            <CardDescription>
              Click on a game to analyze betting opportunities
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3 max-h-96 overflow-y-auto">
              {(() => {
                // Show ALL upcoming games, interleaved by sport
                const nflGames = upcomingGames.filter(g => g.sport_key === 'americanfootball_nfl');
                const ncaafGames = upcomingGames.filter(g => g.sport_key === 'americanfootball_ncaaf');
                
                // Interleave NFL and NCAAF games
                const mixedGames = [];
                const maxLength = Math.max(nflGames.length, ncaafGames.length);
                
                for (let i = 0; i < maxLength; i++) {
                  if (i < nflGames.length) mixedGames.push(nflGames[i]);
                  if (i < ncaafGames.length) mixedGames.push(ncaafGames[i]);
                }
                
                console.log('Dashboard display - NFL games:', nflGames.length, 'NCAAF games:', ncaafGames.length, 'Mixed total:', mixedGames.length);
                
                return mixedGames;
              })().map((game, index) => (
                <div 
                  key={index}
                  className="flex items-center justify-between p-3 border rounded-lg cursor-pointer hover:bg-muted/50 transition-colors"
                  onClick={() => analyzeGame(game)}
                >
                  <div className="flex-1">
                    <div className="font-medium">
                      {game.away_team} @ {game.home_team}
                    </div>
                    <div className="text-sm text-muted-foreground flex items-center gap-2">
                      <Badge variant="outline" className="text-xs">
                        {game.sport_key === 'americanfootball_nfl' ? 'NFL' : 'NCAAF'}
                      </Badge>
                      <Badge className={`text-xs ${getGameStatus(game.commence_time).color}`}>
                        {getGameStatus(game.commence_time).label}
                      </Badge>
                      {formatGameTime(game.commence_time)}
                    </div>
                  </div>
                  {game.predictions && (
                    <div className="text-right mr-2">
                      <div className="text-sm font-medium text-green-600">
                        {(game.predictions.confidence_score * 100).toFixed(1)}%
                      </div>
                      <div className="text-xs text-muted-foreground">
                        Confidence
                      </div>
                    </div>
                  )}
                  <ChevronRight className="h-4 w-4 text-muted-foreground" />
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Game Analysis */}
        <Card>
          <CardHeader>
            <CardTitle>Game Analysis</CardTitle>
            <CardDescription>
              {selectedGame ? `${selectedGame.away_team} @ ${selectedGame.home_team}` : 'Select a game to view analysis'}
            </CardDescription>
          </CardHeader>
          <CardContent>
            {analyzing ? (
              <div className="flex items-center justify-center py-8">
                <RefreshCw className="h-6 w-6 animate-spin mr-2" />
                Analyzing game...
              </div>
            ) : selectedGame && predictions ? (
              <Tabs defaultValue="predictions" className="w-full">
                <TabsList className="grid w-full grid-cols-5">
                  <TabsTrigger value="predictions">Predictions</TabsTrigger>
                  <TabsTrigger value="odds">Current Lines</TabsTrigger>
                  <TabsTrigger value="spread">Spread</TabsTrigger>
                  <TabsTrigger value="ev">Expected Value</TabsTrigger>
                  <TabsTrigger value="summary">Summary</TabsTrigger>
                </TabsList>

                <TabsContent value="predictions" className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {(predictions.home_win_probability * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {selectedGame.home_team} Win
                      </div>
                    </div>
                    <div className="text-center">
                      <div className="text-2xl font-bold">
                        {(predictions.away_win_probability * 100).toFixed(1)}%
                      </div>
                      <div className="text-sm text-muted-foreground">
                        {selectedGame.away_team} Win
                      </div>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <div className="flex justify-between">
                      <span>Predicted Spread:</span>
                      <span className="font-medium">
                        {predictions.predicted_spread > 0 ? '+' : ''}{predictions.predicted_spread.toFixed(1)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>Predicted Total:</span>
                      <span className="font-medium">{predictions.predicted_total.toFixed(1)}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>Confidence:</span>
                      <span className="font-medium">
                        {(predictions.confidence_score * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>

                  {predictions.key_factors && (
                    <div>
                      <h4 className="font-medium mb-2">Key Factors:</h4>
                      <ul className="text-sm space-y-1">
                        {predictions.key_factors.map((factor, index) => (
                          <li key={index} className="flex items-center gap-2">
                            <CheckCircle className="h-3 w-3 text-green-500" />
                            {factor}
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="odds" className="space-y-4">
                  {bettingSummary && bettingSummary.live_odds ? (
                    <div className="space-y-4">
                      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Moneyline Odds */}
                        <Card>
                          <CardHeader className="pb-2">
                            <CardTitle className="text-sm flex items-center gap-2">
                              <DollarSign className="h-4 w-4" />
                              Moneyline (Current Lines)
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-3">
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">{selectedGame.home_team}:</span>
                              <span className={`font-bold ${bettingSummary.live_odds.best_odds?.moneyline?.home > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {formatOdds(bettingSummary.live_odds.best_odds?.moneyline?.home)}
                              </span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">{selectedGame.away_team}:</span>
                              <span className={`font-bold ${bettingSummary.live_odds.best_odds?.moneyline?.away > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {formatOdds(bettingSummary.live_odds.best_odds?.moneyline?.away)}
                              </span>
                            </div>
                            <div className="pt-2 border-t text-xs text-muted-foreground">
                              <div>Home Implied: {bettingSummary.live_odds.best_odds?.moneyline?.home ? 
                                ((bettingSummary.live_odds.best_odds.moneyline.home > 0 ? 
                                  100 / (bettingSummary.live_odds.best_odds.moneyline.home + 100) : 
                                  Math.abs(bettingSummary.live_odds.best_odds.moneyline.home) / (Math.abs(bettingSummary.live_odds.best_odds.moneyline.home) + 100)) * 100).toFixed(1) : '0'}%</div>
                              <div>Away Implied: {bettingSummary.live_odds.best_odds?.moneyline?.away ? 
                                ((bettingSummary.live_odds.best_odds.moneyline.away > 0 ? 
                                  100 / (bettingSummary.live_odds.best_odds.moneyline.away + 100) : 
                                  Math.abs(bettingSummary.live_odds.best_odds.moneyline.away) / (Math.abs(bettingSummary.live_odds.best_odds.moneyline.away) + 100)) * 100).toFixed(1) : '0'}%</div>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Spread Odds */}
                        <Card>
                          <CardHeader className="pb-2">
                            <CardTitle className="text-sm flex items-center gap-2">
                              <Target className="h-4 w-4" />
                              Point Spread
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-3">
                            <div className="text-center">
                              <div className="text-lg font-bold">
                                {bettingSummary.live_odds.best_odds?.spread?.line ? 
                                  (bettingSummary.live_odds.best_odds.spread.line > 0 ? 
                                    `+${bettingSummary.live_odds.best_odds.spread.line}` : 
                                    bettingSummary.live_odds.best_odds.spread.line) : 'N/A'}
                              </div>
                              <div className="text-xs text-muted-foreground">Spread Line</div>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">{selectedGame.home_team}:</span>
                              <span className={`font-bold ${bettingSummary.live_odds.best_odds?.spread?.home > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {formatOdds(bettingSummary.live_odds.best_odds?.spread?.home)}
                              </span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">{selectedGame.away_team}:</span>
                              <span className={`font-bold ${bettingSummary.live_odds.best_odds?.spread?.away > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {formatOdds(bettingSummary.live_odds.best_odds?.spread?.away)}
                              </span>
                            </div>
                          </CardContent>
                        </Card>

                        {/* Totals Odds */}
                        <Card>
                          <CardHeader className="pb-2">
                            <CardTitle className="text-sm flex items-center gap-2">
                              <Activity className="h-4 w-4" />
                              Over/Under
                            </CardTitle>
                          </CardHeader>
                          <CardContent className="space-y-3">
                            <div className="text-center">
                              <div className="text-lg font-bold">
                                {bettingSummary.live_odds.best_odds?.totals?.line || 'N/A'}
                              </div>
                              <div className="text-xs text-muted-foreground">Total Points</div>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Over:</span>
                              <span className={`font-bold ${bettingSummary.live_odds.best_odds?.totals?.over > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {formatOdds(bettingSummary.live_odds.best_odds?.totals?.over)}
                              </span>
                            </div>
                            <div className="flex justify-between items-center">
                              <span className="text-sm font-medium">Under:</span>
                              <span className={`font-bold ${bettingSummary.live_odds.best_odds?.totals?.under > 0 ? 'text-green-600' : 'text-red-600'}`}>
                                {formatOdds(bettingSummary.live_odds.best_odds?.totals?.under)}
                              </span>
                            </div>
                          </CardContent>
                        </Card>
                      </div>

                      {/* Odds Comparison with Predictions */}
                      <Card>
                        <CardHeader>
                          <CardTitle className="text-sm">Odds vs Predictions Analysis</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div>
                              <h4 className="font-medium mb-2">Market Comparison</h4>
                              <div className="space-y-2 text-sm">
                                <div className="flex justify-between">
                                  <span>Sportsbook Spread:</span>
                                  <span className="font-medium">
                                    {bettingSummary.live_odds.best_odds?.spread?.line || 'N/A'}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Predicted Spread:</span>
                                  <span className="font-medium">
                                    {predictions.predicted_spread > 0 ? '+' : ''}{predictions.predicted_spread.toFixed(1)}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Sportsbook Total:</span>
                                  <span className="font-medium">
                                    {bettingSummary.live_odds.best_odds?.totals?.line || 'N/A'}
                                  </span>
                                </div>
                                <div className="flex justify-between">
                                  <span>Predicted Total:</span>
                                  <span className="font-medium">
                                    {predictions.predicted_total.toFixed(1)}
                                  </span>
                                </div>
                              </div>
                            </div>
                            <div>
                              <h4 className="font-medium mb-2">Value Opportunities</h4>
                              <div className="space-y-2">
                                {evCalculations && Object.entries(evCalculations).map(([market, data]) => (
                                  data.ev_percentage > 2 && (
                                    <div key={market} className="flex justify-between items-center p-2 bg-muted rounded">
                                      <span className="text-sm capitalize">{market.replace('_', ' ')}</span>
                                      <Badge className={getRecommendationColor(data.recommendation)}>
                                        {data.ev_percentage.toFixed(1)}% EV
                                      </Badge>
                                    </div>
                                  )
                                ))}
                                {(!evCalculations || !Object.values(evCalculations).some(data => data.ev_percentage > 2)) && (
                                  <div className="text-sm text-muted-foreground">No high-value opportunities identified</div>
                                )}
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      <AlertTriangle className="h-8 w-8 mx-auto mb-2" />
                      <div>Current betting lines not available for this game</div>
                      <div className="text-sm mt-1">Analysis is based on predictions only</div>
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="spread" className="space-y-4">
                  <div className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Predicted Spread</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">
                            {predictions.predicted_spread > 0 ? '+' : ''}{predictions.predicted_spread.toFixed(1)}
                          </div>
                          <div className="text-sm text-muted-foreground">
                            {predictions.predicted_spread > 0 ? selectedGame.home_team : selectedGame.away_team} favored
                          </div>
                        </CardContent>
                      </Card>
                      
                      <Card>
                        <CardHeader className="pb-2">
                          <CardTitle className="text-sm">Spread Confidence</CardTitle>
                        </CardHeader>
                        <CardContent>
                          <div className="text-2xl font-bold">
                            {(predictions.confidence_score * 100).toFixed(1)}%
                          </div>
                          <div className="text-sm text-muted-foreground">
                            Model confidence
                          </div>
                        </CardContent>
                      </Card>
                    </div>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-sm">Spread Analysis</CardTitle>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex justify-between">
                          <span>Sportsbook Spread:</span>
                          <span className="font-medium">
                            {bettingSummary?.best_bets?.find(bet => bet.market_type === 'spread')?.line || 
                             selectedGame.spread || 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Predicted Spread:</span>
                          <span className="font-medium">
                            {selectedGame.away_team} {predictions.predicted_spread > 0 ? '+' : ''}{predictions.predicted_spread.toFixed(1)}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Moneyline:</span>
                          <span className="font-medium text-xs">
                            {selectedGame.home_team}: {bettingSummary?.best_bets?.find(bet => bet.market_type === 'moneyline' && bet.team === selectedGame.home_team)?.odds || selectedGame.home_odds || 'N/A'} | 
                            {selectedGame.away_team}: {bettingSummary?.best_bets?.find(bet => bet.market_type === 'moneyline' && bet.team === selectedGame.away_team)?.odds || selectedGame.away_odds || 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Over/Under:</span>
                          <span className="font-medium">
                            {bettingSummary?.best_bets?.find(bet => bet.market_type === 'totals')?.line || 
                             selectedGame.total || 'N/A'}
                          </span>
                        </div>
                        <div className="flex justify-between">
                          <span>Implied Probability:</span>
                          <span className="font-medium">
                            {predictions.predicted_spread > 0 ? 
                              `${selectedGame.home_team} ${(predictions.home_win_probability * 100).toFixed(1)}%` :
                              `${selectedGame.away_team} ${(predictions.away_win_probability * 100).toFixed(1)}%`
                            }
                          </span>
                        </div>
                        
                        {predictions.predicted_spread !== 0 && (
                          <div className="mt-4 p-3 bg-muted rounded-lg">
                            <div className="text-sm font-medium mb-1">Spread Recommendation:</div>
                            <div className="text-sm text-muted-foreground">
                              {Math.abs(predictions.predicted_spread) > 3 ? 
                                `Strong ${predictions.predicted_spread > 0 ? selectedGame.home_team : selectedGame.away_team} advantage expected` :
                                "Close game expected - spread betting carries higher risk"
                              }
                            </div>
                          </div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="ev" className="space-y-4">
                  {evCalculations && Object.keys(evCalculations).length > 0 ? (
                    <div className="space-y-4">
                      <ResponsiveContainer width="100%" height={200}>
                        <BarChart data={prepareEVChartData()}>
                          <CartesianGrid strokeDasharray="3 3" />
                          <XAxis dataKey="market" />
                          <YAxis />
                          <Tooltip />
                          <Bar dataKey="ev" fill="#8884d8" />
                        </BarChart>
                      </ResponsiveContainer>

                      <div className="space-y-3">
                        {Object.entries(evCalculations).filter(([market]) => market !== 'spread').map(([market, data]) => (
                          <div key={market} className="flex justify-between items-center p-3 border rounded">
                            <div>
                              <div className="font-medium capitalize">
                                {market.replace('_', ' ')}
                              </div>
                              <div className="text-sm text-muted-foreground">
                                EV: {data.ev_percentage.toFixed(2)}%
                              </div>
                            </div>
                            <Badge className={getRecommendationColor(data.recommendation)}>
                              {data.recommendation.replace('_', ' ')}
                            </Badge>
                          </div>
                        ))}
                        
                        {/* Spread EV in its own section */}
                        {evCalculations.spread && (
                          <Card>
                            <CardHeader className="pb-2">
                              <CardTitle className="text-sm">Spread Expected Value</CardTitle>
                            </CardHeader>
                            <CardContent>
                              <div className="flex justify-between items-center">
                                <div>
                                  <div className="font-medium">Spread Betting EV</div>
                                  <div className="text-sm text-muted-foreground">
                                    EV: {evCalculations.spread.ev_percentage.toFixed(2)}%
                                  </div>
                                </div>
                                <Badge className={getRecommendationColor(evCalculations.spread.recommendation)}>
                                  {evCalculations.spread.recommendation.replace('_', ' ')}
                                </Badge>
                              </div>
                            </CardContent>
                          </Card>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No EV calculations available
                    </div>
                  )}
                </TabsContent>

                <TabsContent value="summary" className="space-y-4">
                  {bettingSummary ? (
                    <div className="space-y-4">
                      {bettingSummary.best_bets && bettingSummary.best_bets.length > 0 ? (
                        <div>
                          <h4 className="font-medium mb-3">Best Betting Opportunities</h4>
                          <div className="space-y-3">
                            {bettingSummary.best_bets.slice(0, 4).map((bet, index) => (
                              <div key={index} className="p-3 border rounded-lg">
                                <div className="flex justify-between items-center p-3 border rounded">
                                  <div>
                                    <span className="font-medium capitalize">
                                      {bet.market === 'spread' ? 'Point Spread' : bet.market.replace('_', ' ')}
                                    </span>
                                    {bet.line && (
                                      <div className="text-xs text-muted-foreground">
                                        Line: {bet.line} | Odds: {formatOdds(bet.odds)}
                                      </div>
                                    )}
                                  </div>
                                  <Badge className={getRecommendationColor(bet.recommendation)}>
                                    {bet.recommendation.replace('_', ' ')}
                                  </Badge>
                                </div>
                                <div className="grid grid-cols-2 gap-2 text-sm">
                                  <div>EV: {bet.ev_percentage.toFixed(2)}%</div>
                                  <div>Edge: {bet.edge_percentage.toFixed(2)}%</div>
                                  <div>True Prob: {(bet.true_probability * 100).toFixed(1)}%</div>
                                  <div>Implied Prob: {(bet.implied_probability * 100).toFixed(1)}%</div>
                                </div>
                                {bet.kelly_info && (
                                  <div className="mt-2 text-sm text-muted-foreground">
                                    Recommended bet: {formatCurrency(bet.kelly_info.recommended_bet)}
                                  </div>
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <Alert>
                          <AlertTriangle className="h-4 w-4" />
                          <AlertDescription>
                            No profitable betting opportunities identified for this game.
                          </AlertDescription>
                        </Alert>
                      )}

                      {bettingSummary.recommendation_summary && (
                        <div>
                          <h4 className="font-medium mb-2">Summary</h4>
                          <p className="text-sm text-muted-foreground">
                            {bettingSummary.recommendation_summary}
                          </p>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-center py-8 text-muted-foreground">
                      No betting summary available
                    </div>
                  )}
                </TabsContent>
              </Tabs>
            ) : (
              <div className="text-center py-8 text-muted-foreground">
                Select a game from the list to view detailed analysis
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default Dashboard;

