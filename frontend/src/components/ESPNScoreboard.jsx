import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Clock, 
  Trophy, 
  Calendar, 
  Activity,
  RefreshCw,
  Wifi,
  WifiOff
} from 'lucide-react';
import { api } from '@/lib/api';

const ESPNScoreboard = ({ scoreboardData: propScoreboardData, onRefresh, isLoading: propIsLoading }) => {
  const [localScoreboardData, setLocalScoreboardData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [lastUpdate, setLastUpdate] = useState(null);
  const [selectedLeague, setSelectedLeague] = useState('all');

  // Use prop data if available, otherwise fetch locally
  const scoreboardData = propScoreboardData || localScoreboardData;
  const loading = propIsLoading || isLoading;

  const fetchScoreboardData = async () => {
    if (onRefresh) {
      onRefresh();
      return;
    }
    
    setIsLoading(true);
    setError(null);
    
    try {
      const result = await api.espn.getScoreboard({ days: 10 });
      
      if (result && result.success) {
        setLocalScoreboardData(result.data);
        setLastUpdate(new Date().toLocaleTimeString());
      } else {
        setError('Failed to fetch scoreboard data');
      }
    } catch (err) {
      setError(`Error: ${err.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    if (!propScoreboardData) {
      fetchScoreboardData();
      // Auto-refresh every 30 seconds only if not using prop data
      const interval = setInterval(fetchScoreboardData, 30000);
      return () => clearInterval(interval);
    }
  }, [propScoreboardData]);


  const formatTime = (timeString) => {
    if (!timeString) return 'TBD';
    try {
      const date = new Date(timeString);
      return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { 
        hour: '2-digit', 
        minute: '2-digit' 
      });
    } catch {
      return timeString;
    }
  };

  const getStatusBadge = (status) => {
    switch (status) {
      case 'LIVE':
        return <Badge variant="destructive" className="animate-pulse">LIVE</Badge>;
      case 'FINAL':
        return <Badge variant="secondary">FINAL</Badge>;
      case 'SCHEDULED':
        return <Badge variant="outline">SCHEDULED</Badge>;
      default:
        return <Badge variant="outline">{status}</Badge>;
    }
  };

  const GameCard = ({ game }) => (
    <Card className="mb-4 hover:shadow-md transition-shadow">
      <CardContent className="p-4">
        <div className="flex justify-between items-center mb-2">
          <div className="flex items-center gap-2">
            <Badge variant="outline" className="text-xs">
              {game.sport_title}
            </Badge>
            {getStatusBadge(game.status)}
          </div>
          <div className="text-sm text-muted-foreground">
            {game.status === 'SCHEDULED' ? formatTime(game.commence_time) : 
             game.status === 'FINAL' ? 'Final' : 'Live'}
          </div>
        </div>
        
        <div className="grid grid-cols-3 gap-4 items-center">
          {/* Away Team */}
          <div className="text-right">
            <div className="font-semibold text-sm">{game.away_team}</div>
            {game.away_score !== null && (
              <div className="text-2xl font-bold">{game.away_score}</div>
            )}
          </div>
          
          {/* VS or Score Separator */}
          <div className="text-center">
            <div className="text-muted-foreground text-sm">
              {game.status === 'SCHEDULED' ? 'vs' : '@'}
            </div>
          </div>
          
          {/* Home Team */}
          <div className="text-left">
            <div className="font-semibold text-sm">{game.home_team}</div>
            {game.home_score !== null && (
              <div className="text-2xl font-bold">{game.home_score}</div>
            )}
          </div>
        </div>
        
        {game.formatted_time && game.status === 'SCHEDULED' && (
          <div className="text-xs text-muted-foreground mt-2 text-center">
            {game.formatted_time}
          </div>
        )}
      </CardContent>
    </Card>
  );

  const renderGames = (games, category) => {
    console.log(`Rendering ${category} games:`, games?.length || 0, games);
    
    if (!games || games.length === 0) {
      return (
        <div className="text-center py-8 text-muted-foreground">
          No {category.toLowerCase()} games available
        </div>
      );
    }

    return (
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {games.map((game, index) => (
          <GameCard key={`${game.id || index}`} game={game} />
        ))}
      </div>
    );
  };

  const getFilteredGames = (games) => {
    if (!games) return [];
    
    switch (selectedLeague) {
      case 'nfl':
        return games.filter(game => game.sport_key === 'americanfootball_nfl');
      case 'ncaaf':
        return games.filter(game => game.sport_key === 'americanfootball_ncaaf');
      default:
        return games;
    }
  };

  if (loading && !scoreboardData) {
    return (
      <Card>
        <CardContent className="p-8 text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p>Loading ESPN-style scoreboard...</p>
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <WifiOff className="h-4 w-4" />
        <AlertDescription>
          {error}
          <Button 
            variant="outline" 
            size="sm" 
            onClick={fetchScoreboardData}
            className="ml-2"
          >
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <Card>
        <CardHeader>
          <div className="flex justify-between items-center">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Trophy className="h-5 w-5" />
                ESPN-Style Scoreboard
              </CardTitle>
              <CardDescription>
                Live NFL and NCAAF games, scores, and schedules
              </CardDescription>
            </div>
            <div className="flex items-center gap-2">
              {lastUpdate && (
                <div className="text-sm text-muted-foreground flex items-center gap-1">
                  <Wifi className="h-4 w-4" />
                  Updated: {lastUpdate}
                </div>
              )}
              <Button 
                variant="outline" 
                size="sm" 
                onClick={fetchScoreboardData}
                disabled={isLoading}
              >
                <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      {/* Summary Stats */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-red-600">
              {((scoreboardData?.live?.nfl?.length || 0) + (scoreboardData?.live?.ncaaf?.length || 0))}
            </div>
            <div className="text-sm text-muted-foreground">Live Games</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-blue-600">
              {((scoreboardData?.upcoming?.nfl?.length || 0) + (scoreboardData?.upcoming?.ncaaf?.length || 0))}
            </div>
            <div className="text-sm text-muted-foreground">Upcoming</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold text-green-600">
              {((scoreboardData?.completed?.nfl?.length || 0) + (scoreboardData?.completed?.ncaaf?.length || 0))}
            </div>
            <div className="text-sm text-muted-foreground">Completed</div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <div className="text-2xl font-bold">
              {scoreboardData?.summary?.total_games || 0}
            </div>
            <div className="text-sm text-muted-foreground">Total Games</div>
          </CardContent>
        </Card>
      </div>


      {/* League Filter */}
      <div className="flex gap-2">
        <Button
          variant={selectedLeague === 'all' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setSelectedLeague('all')}
        >
          All ({scoreboardData?.summary?.total_games || 0})
        </Button>
        <Button
          variant={selectedLeague === 'nfl' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setSelectedLeague('nfl')}
        >
          NFL ({scoreboardData?.summary?.nfl_games || 0})
        </Button>
        <Button
          variant={selectedLeague === 'ncaaf' ? 'default' : 'outline'}
          size="sm"
          onClick={() => setSelectedLeague('ncaaf')}
        >
          NCAAF ({scoreboardData?.summary?.ncaaf_games || 0})
        </Button>
      </div>

      {/* Games Tabs */}
      <Tabs defaultValue="live" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="live" className="flex items-center gap-2">
            <Activity className="h-4 w-4" />
            Live ({(scoreboardData?.live?.nfl?.length || 0) + (scoreboardData?.live?.ncaaf?.length || 0)})
          </TabsTrigger>
          <TabsTrigger value="upcoming" className="flex items-center gap-2">
            <Clock className="h-4 w-4" />
            Upcoming ({(scoreboardData?.upcoming?.nfl?.length || 0) + (scoreboardData?.upcoming?.ncaaf?.length || 0)})
          </TabsTrigger>
          <TabsTrigger value="completed" className="relative">
            Completed
            <Badge variant="secondary" className="ml-2">
              {scoreboardData?.completed ? 
                ((scoreboardData.completed.nfl?.length || 0) + (scoreboardData.completed.ncaaf?.length || 0)) : 0}
            </Badge>
          </TabsTrigger>
        </TabsList>

        <TabsContent value="live" className="space-y-4">
          <div className="grid gap-4">
            {/* Emergency fix: Only show games without scores or with status explicitly LIVE */}
            {scoreboardData?.live?.nfl?.filter(game => {
              console.log('NFL Live game filter:', {
                teams: `${game.away_team} @ ${game.home_team}`,
                home_score: game.home_score,
                away_score: game.away_score,
                status: game.status
              });
              
              // Only show games that don't have final scores
              if (game.home_score && game.away_score) {
                console.log('Filtering out game with scores:', `${game.away_team} @ ${game.home_team}`);
                return false;
              }
              return true;
            }).map((game, index) => (
              <GameCard key={`${game.id || index}`} game={game} />
            ))}
            {scoreboardData?.live?.ncaaf?.filter(game => {
              console.log('NCAAF Live game filter:', {
                teams: `${game.away_team} @ ${game.home_team}`,
                home_score: game.home_score,
                away_score: game.away_score,
                status: game.status
              });
              
              // Only show games that don't have final scores
              if (game.home_score && game.away_score) {
                console.log('Filtering out NCAAF game with scores:', `${game.away_team} @ ${game.home_team}`);
                return false;
              }
              return true;
            }).map((game, index) => (
              <GameCard key={`${game.id || index}`} game={game} />
            ))}
            
            {/* Show message if no live games */}
            {(!scoreboardData?.live?.nfl?.some(game => !(game.home_score && game.away_score)) && 
              !scoreboardData?.live?.ncaaf?.some(game => !(game.home_score && game.away_score))) && (
              <div className="text-center py-8 text-muted-foreground">
                <p>No live games currently in progress</p>
              </div>
            )}
          </div>
        </TabsContent>

        <TabsContent value="upcoming" className="mt-6">
          {renderGames(
            (() => {
              const nflGames = scoreboardData?.upcoming?.nfl || [];
              const ncaafGames = scoreboardData?.upcoming?.ncaaf || [];
              const allGames = [...nflGames, ...ncaafGames];
              
              if (selectedLeague === 'nfl') return nflGames;
              if (selectedLeague === 'ncaaf') return ncaafGames;
              return allGames;
            })(),
            'Upcoming'
          )}
        </TabsContent>

        <TabsContent value="completed" className="mt-6">
          {(() => {
            console.log('Completed tab - scoreboardData:', scoreboardData?.completed);
            const nflGames = scoreboardData?.completed?.nfl || [];
            const ncaafGames = scoreboardData?.completed?.ncaaf || [];
            console.log('NFL completed games:', nflGames.length);
            console.log('NCAAF completed games:', ncaafGames.length);
            const allGames = [...nflGames, ...ncaafGames];
            
            let gamesToShow = allGames;
            if (selectedLeague === 'nfl') gamesToShow = nflGames;
            if (selectedLeague === 'ncaaf') gamesToShow = ncaafGames;
            
            console.log('Games to show in completed tab:', gamesToShow.length);
            return renderGames(gamesToShow, 'Completed');
          })()}
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default ESPNScoreboard;
