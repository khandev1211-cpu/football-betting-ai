import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Calendar, 
  Clock, 
  TrendingUp, 
  TrendingDown, 
  DollarSign,
  Users,
  MapPin,
  RefreshCw
} from 'lucide-react';
import { format, formatDistanceToNow, isToday, isTomorrow } from 'date-fns';

const UpcomingMatches = ({ games = [], onRefresh, isLoading }) => {
  const [sortBy, setSortBy] = useState('date'); // date, ev, prediction
  const [filterBy, setFilterBy] = useState('all'); // all, today, tomorrow, week

  const getDateLabel = (gameDate) => {
    const date = new Date(gameDate);
    if (isToday(date)) return 'Today';
    if (isTomorrow(date)) return 'Tomorrow';
    return format(date, 'MMM dd');
  };

  const getTimeUntilGame = (gameDate) => {
    const date = new Date(gameDate);
    return formatDistanceToNow(date, { addSuffix: true });
  };

  const getPredictionColor = (prediction) => {
    if (!prediction) return 'text-gray-500';
    const confidence = prediction.confidence || 0;
    if (confidence >= 0.7) return 'text-green-600';
    if (confidence >= 0.6) return 'text-yellow-600';
    return 'text-red-600';
  };

  const getEVColor = (ev) => {
    if (!ev) return 'text-gray-500';
    if (ev > 5) return 'text-green-600 font-bold';
    if (ev > 0) return 'text-green-500';
    return 'text-red-500';
  };

  const filteredAndSortedGames = games
    .filter(game => {
      const gameDate = new Date(game.commence_time);
      const now = new Date();
      
      switch (filterBy) {
        case 'today':
          return isToday(gameDate);
        case 'tomorrow':
          return isTomorrow(gameDate);
        case 'week':
          const weekFromNow = new Date(now.getTime() + 7 * 24 * 60 * 60 * 1000);
          return gameDate <= weekFromNow;
        default:
          return true;
      }
    })
    .sort((a, b) => {
      switch (sortBy) {
        case 'ev':
          const aEV = a.best_ev?.max_ev || 0;
          const bEV = b.best_ev?.max_ev || 0;
          return bEV - aEV;
        case 'prediction':
          const aConf = a.prediction?.confidence || 0;
          const bConf = b.prediction?.confidence || 0;
          return bConf - aConf;
        default:
          return new Date(a.commence_time) - new Date(b.commence_time);
      }
    });

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Calendar className="h-6 w-6" />
            Upcoming Matches
          </h2>
          <p className="text-muted-foreground">
            {filteredAndSortedGames.length} games scheduled
          </p>
        </div>
        
        <div className="flex flex-wrap gap-2">
          {/* Filter Buttons */}
          <div className="flex gap-1">
            {['all', 'today', 'tomorrow', 'week'].map((filter) => (
              <Button
                key={filter}
                variant={filterBy === filter ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterBy(filter)}
              >
                {filter.charAt(0).toUpperCase() + filter.slice(1)}
              </Button>
            ))}
          </div>
          
          {/* Sort Buttons */}
          <div className="flex gap-1">
            {[
              { key: 'date', label: 'Date', icon: Clock },
              { key: 'ev', label: 'EV', icon: DollarSign },
              { key: 'prediction', label: 'Confidence', icon: TrendingUp }
            ].map(({ key, label, icon: Icon }) => (
              <Button
                key={key}
                variant={sortBy === key ? 'default' : 'outline'}
                size="sm"
                onClick={() => setSortBy(key)}
              >
                <Icon className="h-3 w-3 mr-1" />
                {label}
              </Button>
            ))}
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={isLoading}
          >
            <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          </Button>
        </div>
      </div>

      {/* Games Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filteredAndSortedGames.map((game, index) => (
          <Card key={game.id || index} className="hover:shadow-lg transition-shadow">
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start">
                <div className="space-y-1">
                  <Badge variant="outline" className="text-xs">
                    {getDateLabel(game.commence_time)}
                  </Badge>
                  <div className="flex items-center gap-1 text-xs text-muted-foreground">
                    <Clock className="h-3 w-3" />
                    {format(new Date(game.commence_time), 'h:mm a')}
                  </div>
                </div>
                <div className="text-right">
                  <div className="text-xs text-muted-foreground">
                    {getTimeUntilGame(game.commence_time)}
                  </div>
                  {game.sport_title && (
                    <Badge variant="secondary" className="text-xs mt-1">
                      {game.sport_title}
                    </Badge>
                  )}
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {/* Teams */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{game.away_team}</span>
                  </div>
                  {game.prediction?.away_win_prob && (
                    <span className={`text-sm ${getPredictionColor(game.prediction)}`}>
                      {(game.prediction.away_win_prob * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
                
                <div className="text-center text-xs text-muted-foreground">vs</div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Users className="h-4 w-4 text-muted-foreground" />
                    <span className="font-medium">{game.home_team}</span>
                  </div>
                  {game.prediction?.home_win_prob && (
                    <span className={`text-sm ${getPredictionColor(game.prediction)}`}>
                      {(game.prediction.home_win_prob * 100).toFixed(1)}%
                    </span>
                  )}
                </div>
              </div>

              {/* Venue */}
              {game.venue && (
                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                  <MapPin className="h-3 w-3" />
                  <span className="truncate">{game.venue}</span>
                </div>
              )}

              {/* Prediction Summary */}
              {game.prediction && (
                <div className="bg-muted/50 rounded-lg p-3 space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">AI Prediction</span>
                    <Badge 
                      variant={game.prediction.confidence > 0.7 ? 'default' : 'secondary'}
                      className="text-xs"
                    >
                      {(game.prediction.confidence * 100).toFixed(0)}% confident
                    </Badge>
                  </div>
                  
                  <div className="text-sm">
                    <span className="font-medium">
                      {game.prediction.predicted_winner}
                    </span>
                    {game.prediction.spread && (
                      <span className="text-muted-foreground ml-2">
                        ({game.prediction.spread > 0 ? '+' : ''}{game.prediction.spread})
                      </span>
                    )}
                  </div>
                </div>
              )}

              {/* Best EV */}
              {game.best_ev && (
                <div className="bg-green-50 dark:bg-green-950/20 rounded-lg p-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Best EV</span>
                    <div className="flex items-center gap-1">
                      {game.best_ev.max_ev > 0 ? (
                        <TrendingUp className="h-3 w-3 text-green-600" />
                      ) : (
                        <TrendingDown className="h-3 w-3 text-red-600" />
                      )}
                      <span className={`text-sm font-bold ${getEVColor(game.best_ev.max_ev)}`}>
                        {game.best_ev.max_ev > 0 ? '+' : ''}{game.best_ev.max_ev.toFixed(2)}%
                      </span>
                    </div>
                  </div>
                  
                  {game.best_ev.market && (
                    <div className="text-xs text-muted-foreground mt-1">
                      {game.best_ev.market} • {game.best_ev.bookmaker}
                    </div>
                  )}
                  
                  {game.best_ev.kelly_bet && (
                    <div className="text-xs text-green-700 dark:text-green-400 mt-1">
                      Kelly: ${game.best_ev.kelly_bet.toFixed(0)}
                    </div>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {filteredAndSortedGames.length === 0 && (
        <Card className="text-center py-12">
          <CardContent>
            <Calendar className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No upcoming matches</h3>
            <p className="text-muted-foreground mb-4">
              {filterBy === 'all' 
                ? 'No games are currently scheduled.' 
                : `No games found for ${filterBy}.`
              }
            </p>
            <Button onClick={onRefresh} disabled={isLoading}>
              <RefreshCw className={`h-4 w-4 mr-2 ${isLoading ? 'animate-spin' : ''}`} />
              Refresh Data
            </Button>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default UpcomingMatches;
