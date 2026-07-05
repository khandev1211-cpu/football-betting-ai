import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Radio, 
  Clock, 
  TrendingUp, 
  TrendingDown, 
  DollarSign,
  Users,
  Activity,
  RefreshCw,
  Zap,
  Timer,
  Target,
  Wifi,
  WifiOff,
  Brain,
  AlertCircle
} from 'lucide-react';
import { useSocket } from '@/hooks/useSocket';

const LiveMatches = ({ liveGames = [], onRefresh, isLoading }) => {
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [lastUpdate, setLastUpdate] = useState(new Date());
  const [selectedGame, setSelectedGame] = useState(null);
  
  // Socket.IO integration for real-time data
  const {
    isConnected,
    connectionError,
    liveGames: socketLiveGames,
    liveOpportunities,
    gameAnalysis,
    analysisLoading,
    subscribeToGame,
    unsubscribeFromGame,
    requestAnalysis,
    refreshOpportunities
  } = useSocket();

  // Use socket data if available, fallback to props
  const displayGames = socketLiveGames.length > 0 ? socketLiveGames : liveGames;

  // Subscribe to all live games for real-time updates
  useEffect(() => {
    displayGames.forEach(game => {
      if (game.game_id) {
        subscribeToGame(game.game_id);
      }
    });

    return () => {
      displayGames.forEach(game => {
        if (game.game_id) {
          unsubscribeFromGame(game.game_id);
        }
      });
    };
  }, [displayGames, subscribeToGame, unsubscribeFromGame]);

  // Auto-refresh opportunities every 30 seconds
  useEffect(() => {
    if (!autoRefresh || !isConnected) return;
    
    const interval = setInterval(() => {
      refreshOpportunities();
      setLastUpdate(new Date());
    }, 30000);
    
    return () => clearInterval(interval);
  }, [autoRefresh, isConnected, refreshOpportunities]);

  const getGameStatus = (game) => {
    if (game.status === 'live' || game.status === 'in_progress') {
      return {
        label: 'LIVE',
        color: 'bg-red-500 text-white',
        icon: Radio,
        pulse: true
      };
    }
    if (game.status === 'halftime') {
      return {
        label: 'HALFTIME',
        color: 'bg-yellow-500 text-white',
        icon: Timer,
        pulse: false
      };
    }
    if (game.status === 'final' || game.status === 'completed') {
      return {
        label: 'FINAL',
        color: 'bg-gray-500 text-white',
        icon: Target,
        pulse: false
      };
    }
    return {
      label: 'UNKNOWN',
      color: 'bg-gray-400 text-white',
      icon: Activity,
      pulse: false
    };
  };

  const getScoreColor = (score, opponentScore, isHome = false) => {
    if (score > opponentScore) return 'text-green-600 font-bold';
    if (score < opponentScore) return 'text-red-600';
    return 'text-gray-600';
  };

  const getGameProgress = (game) => {
    if (!game.period || !game.time_remaining) return 0;
    
    // Estimate progress based on period and time
    const totalPeriods = game.sport_key?.includes('basketball') ? 4 : 4; // quarters
    const periodProgress = ((game.period - 1) / totalPeriods) * 100;
    
    // Add progress within current period (rough estimate)
    const periodTimeProgress = game.time_remaining ? 
      ((15 - parseFloat(game.time_remaining)) / 15) * (100 / totalPeriods) : 0;
    
    return Math.min(100, periodProgress + periodTimeProgress);
  };

  const getEVColor = (ev) => {
    if (!ev) return 'text-gray-500';
    if (ev > 5) return 'text-green-600 font-bold';
    if (ev > 0) return 'text-green-500';
    return 'text-red-500';
  };

  const sortedLiveGames = liveGames.sort((a, b) => {
    // Prioritize live games, then by start time
    const statusPriority = { live: 0, in_progress: 0, halftime: 1, final: 2, completed: 2 };
    const aPriority = statusPriority[a.status] || 3;
    const bPriority = statusPriority[b.status] || 3;
    
    if (aPriority !== bPriority) return aPriority - bPriority;
    return new Date(b.commence_time) - new Date(a.commence_time);
  });

  return (
    <div className="space-y-6">
      {/* Connection Status Alert */}
      {connectionError && (
        <Alert variant="destructive" className="mb-4">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Real-time connection error: {connectionError}
            <Button variant="outline" size="sm" className="ml-2" onClick={() => window.location.reload()}>
              Reconnect
            </Button>
          </AlertDescription>
        </Alert>
      )}

      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Radio className="h-6 w-6 text-red-500" />
            Live Matches
            {isConnected ? (
              <Wifi className="h-5 w-5 text-green-500" title="Real-time connected" />
            ) : (
              <WifiOff className="h-5 w-5 text-red-500" title="Real-time disconnected" />
            )}
          </h2>
          <p className="text-muted-foreground">
            {sortedLiveGames.length} games • Updated {lastUpdate.toLocaleTimeString()}
            {isConnected && <span className="text-green-600 ml-2">• Live data</span>}
          </p>
        </div>
        
        <div className="flex items-center gap-2">
          <Button
            variant={autoRefresh ? 'default' : 'outline'}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            disabled={!isConnected}
          >
            <Zap className="h-4 w-4 mr-1" />
            Auto-refresh
          </Button>
          
          <Button
            variant="outline"
            size="sm"
            onClick={() => {
              onRefresh();
              refreshOpportunities();
            }}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={refreshOpportunities}
            disabled={!isConnected}
          >
            <Target className="h-4 w-4 mr-1" />
            Opportunities
          </Button>
        </div>
      </div>

      {/* Live Games Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        {sortedLiveGames.map((game, index) => {
          const status = getGameStatus(game);
          const StatusIcon = status.icon;
          const progress = getGameProgress(game);
          
          return (
            <Card key={game.id || index} className="relative overflow-hidden">
              {/* Live indicator pulse effect */}
              {status.pulse && (
                <div className="absolute top-0 left-0 w-full h-1 bg-red-500 animate-pulse" />
              )}
              
              <CardHeader className="pb-3">
                <div className="flex justify-between items-start">
                  <div className="flex items-center gap-2">
                    <Badge className={`${status.color} ${status.pulse ? 'animate-pulse' : ''}`}>
                      <StatusIcon className="h-3 w-3 mr-1" />
                      {status.label}
                    </Badge>
                    {game.sport_title && (
                      <Badge variant="outline" className="text-xs">
                        {game.sport_title}
                      </Badge>
                    )}
                  </div>
                  
                  <div className="text-right text-xs text-muted-foreground">
                    {game.period && (
                      <div>Q{game.period}</div>
                    )}
                    {game.time_remaining && (
                      <div>{game.time_remaining}</div>
                    )}
                  </div>
                </div>
                
                {/* Game Progress Bar */}
                {progress > 0 && (
                  <Progress value={progress} className="h-1 mt-2" />
                )}
              </CardHeader>
              
              <CardContent className="space-y-4">
                {/* Score Display */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Users className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{game.away_team}</span>
                    </div>
                    <div className="text-right">
                      <div className={`text-2xl font-bold ${getScoreColor(
                        game.away_score || 0, 
                        game.home_score || 0
                      )}`}>
                        {game.away_score || 0}
                      </div>
                      {game.live_odds?.away_odds && (
                        <div className="text-xs text-muted-foreground">
                          {game.live_odds.away_odds > 0 ? '+' : ''}{game.live_odds.away_odds}
                        </div>
                      )}
                    </div>
                  </div>
                  
                  <div className="flex items-center justify-between p-3 bg-muted/50 rounded-lg">
                    <div className="flex items-center gap-3">
                      <Users className="h-4 w-4 text-muted-foreground" />
                      <span className="font-medium">{game.home_team}</span>
                    </div>
                    <div className="text-right">
                      <div className={`text-2xl font-bold ${getScoreColor(
                        game.home_score || 0, 
                        game.away_score || 0,
                        true
                      )}`}>
                        {game.home_score || 0}
                      </div>
                      {game.live_odds?.home_odds && (
                        <div className="text-xs text-muted-foreground">
                          {game.live_odds.home_odds > 0 ? '+' : ''}{game.live_odds.home_odds}
                        </div>
                      )}
                    </div>
                  </div>
                </div>

                {/* Live Betting Opportunities */}
                {game.live_ev && game.live_ev.length > 0 && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium flex items-center gap-1">
                      <DollarSign className="h-3 w-3" />
                      Live Betting Opportunities
                    </h4>
                    {game.live_ev.slice(0, 2).map((ev, evIndex) => (
                      <div key={evIndex} className="bg-green-50 dark:bg-green-950/20 rounded-lg p-2">
                        <div className="flex justify-between items-center">
                          <span className="text-sm font-medium">{ev.market}</span>
                          <div className="flex items-center gap-1">
                            {ev.ev_percentage > 0 ? (
                              <TrendingUp className="h-3 w-3 text-green-600" />
                            ) : (
                              <TrendingDown className="h-3 w-3 text-red-600" />
                            )}
                            <span className={`text-sm font-bold ${getEVColor(ev.ev_percentage)}`}>
                              {ev.ev_percentage > 0 ? '+' : ''}{ev.ev_percentage.toFixed(2)}%
                            </span>
                          </div>
                        </div>
                        <div className="flex justify-between items-center text-xs text-muted-foreground mt-1">
                          <span>{ev.bookmaker}</span>
                          <span>Odds: {ev.odds > 0 ? '+' : ''}{ev.odds}</span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* Game Stats */}
                {(game.stats || game.possession) && (
                  <div className="space-y-2">
                    <h4 className="text-sm font-medium">Live Stats</h4>
                    <div className="grid grid-cols-2 gap-2 text-xs">
                      {game.possession && (
                        <div className="flex justify-between">
                          <span>Possession</span>
                          <span>{game.possession.away}% - {game.possession.home}%</span>
                        </div>
                      )}
                      {game.stats?.total_yards && (
                        <div className="flex justify-between">
                          <span>Total Yards</span>
                          <span>{game.stats.away_yards} - {game.stats.home_yards}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* AI Analysis Section */}
                {gameAnalysis[game.game_id || game.id] && (
                  <div className="space-y-2 pt-2 border-t">
                    <h4 className="text-sm font-medium flex items-center gap-1">
                      <Brain className="h-3 w-3" />
                      AI Analysis
                    </h4>
                    <div className="text-xs space-y-1">
                      {gameAnalysis[game.game_id || game.id].recommendations?.slice(0, 2).map((rec, idx) => (
                        <div key={idx} className="bg-blue-50 dark:bg-blue-950/20 rounded p-2">
                          <div className="font-medium">{rec.market}</div>
                          <div className="text-muted-foreground">
                            EV: {(rec.expected_value * 100).toFixed(1)}% | {rec.recommendation}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                )}

                {/* Quick Actions */}
                <div className="flex gap-2 pt-2 border-t">
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex-1"
                    onClick={() => setSelectedGame(game)}
                  >
                    <Activity className="h-3 w-3 mr-1" />
                    View Details
                  </Button>
                  
                  <Button 
                    variant="outline" 
                    size="sm" 
                    className="flex-1"
                    onClick={() => requestAnalysis(game.game_id || game.id)}
                    disabled={analysisLoading[game.game_id || game.id] || !isConnected}
                  >
                    {analysisLoading[game.game_id || game.id] ? (
                      <RefreshCw className="h-3 w-3 mr-1 animate-spin" />
                    ) : (
                      <Brain className="h-3 w-3 mr-1" />
                    )}
                    AI Analysis
                  </Button>
                  
                  {game.live_ev && game.live_ev.length > 0 && (
                    <Button variant="default" size="sm" className="flex-1">
                      <Target className="h-3 w-3 mr-1" />
                      Place Bet
                    </Button>
                  )}
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {/* Empty State */}
      {sortedLiveGames.length === 0 && (
        <Card className="text-center py-12">
          <CardContent>
            <Radio className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No live matches</h3>
            <p className="text-muted-foreground mb-4">
              There are currently no games in progress. Check back during game times!
            </p>
            <Button onClick={onRefresh} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh Data
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Auto-refresh indicator */}
      {autoRefresh && sortedLiveGames.length > 0 && (
        <div className="text-center">
          <Badge variant="outline" className="text-xs">
            <Zap className="h-3 w-3 mr-1" />
            Auto-refreshing every 30 seconds
          </Badge>
        </div>
      )}
    </div>
  );
};

export default LiveMatches;
