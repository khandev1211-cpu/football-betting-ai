import React, { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  TrendingUp, 
  TrendingDown, 
  DollarSign,
  Target,
  Brain,
  Zap,
  RefreshCw,
  AlertTriangle,
  CheckCircle,
  Clock,
  Percent
} from 'lucide-react';
import { useSocket } from '@/hooks/useSocket';

const LiveOpportunities = ({ onRefresh, isLoading }) => {
  const [sortBy, setSortBy] = useState('ev'); // ev, confidence, time
  const [filterBy, setFilterBy] = useState('all'); // all, strong_bet, good_bet
  const [autoRefresh, setAutoRefresh] = useState(true);

  const {
    isConnected,
    liveOpportunities,
    refreshOpportunities
  } = useSocket();

  // Auto-refresh opportunities
  useEffect(() => {
    if (autoRefresh && isConnected) {
      const interval = setInterval(() => {
        refreshOpportunities();
      }, 15000); // Refresh every 15 seconds for opportunities
      
      return () => clearInterval(interval);
    }
  }, [autoRefresh, isConnected, refreshOpportunities]);

  const getRecommendationColor = (recommendation) => {
    switch (recommendation) {
      case 'STRONG_BET': return 'bg-green-600 text-white';
      case 'GOOD_BET': return 'bg-blue-600 text-white';
      case 'CONSIDER': return 'bg-yellow-600 text-white';
      case 'LOW_CONFIDENCE': return 'bg-orange-500 text-white';
      default: return 'bg-gray-500 text-white';
    }
  };

  const getEVColor = (ev) => {
    if (ev > 0.1) return 'text-green-700 font-bold';
    if (ev > 0.05) return 'text-green-600 font-semibold';
    if (ev > 0.03) return 'text-green-500';
    return 'text-gray-600';
  };

  const processedOpportunities = useMemo(() => {
    if (!liveOpportunities || liveOpportunities.length === 0) return [];
    
    let filtered = liveOpportunities;
    
    // Filter by date - only show games within next 10 days
    const now = new Date();
    const tenDaysFromNow = new Date(now.getTime() + (10 * 24 * 60 * 60 * 1000));
    
    filtered = filtered.filter(opp => {
      if (!opp.commence_time) return false; // Exclude games without date
      const gameDate = new Date(opp.commence_time);
      return gameDate >= now && gameDate <= tenDaysFromNow;
    });
    
    // Apply recommendation filter
    if (filterBy !== 'all') {
      filtered = filtered.filter(opp => opp.recommendation === filterBy.toUpperCase());
    }
    
    // Apply sort
    filtered.sort((a, b) => {
      switch (sortBy) {
        case 'ev':
          return (b.ev_percentage || 0) - (a.ev_percentage || 0);
        case 'confidence':
          return (b.confidence || 0) - (a.confidence || 0);
        case 'time':
          return new Date(a.commence_time || 0) - new Date(b.commence_time || 0);
        default:
          return 0;
      }
    });
    
    return filtered;
  }, [liveOpportunities, sortBy, filterBy]);

  const formatOdds = (odds) => {
    if (!odds) return 'N/A';
    return odds > 0 ? `+${odds}` : `${odds}`;
  };

  const formatMarket = (market) => {
    return market.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
  };

  return (
    <div className="space-y-6">
      {/* Header and Controls */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div>
          <h2 className="text-2xl font-bold flex items-center gap-2">
            <Target className="h-6 w-6 text-green-600" />
            Live Betting Opportunities
          </h2>
          <p className="text-muted-foreground">
            {processedOpportunities.length} opportunities found
            {isConnected && <span className="text-green-600 ml-2">• Real-time</span>}
          </p>
        </div>
        
        <div className="flex flex-wrap gap-2">
          {/* Filter Buttons */}
          <div className="flex gap-1">
            {[
              { key: 'all', label: 'All' },
              { key: 'strong_bet', label: 'Strong Bets' },
              { key: 'good_bet', label: 'Good+ Bets' }
            ].map(({ key, label }) => (
              <Button
                key={key}
                variant={filterBy === key ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterBy(key)}
              >
                {label}
              </Button>
            ))}
          </div>
          
          {/* Sort Buttons */}
          <div className="flex gap-1">
            {[
              { key: 'ev', label: 'EV', icon: DollarSign },
              { key: 'confidence', label: 'Confidence', icon: CheckCircle },
              { key: 'time', label: 'Time', icon: Clock }
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
            variant={autoRefresh ? 'default' : 'outline'}
            size="sm"
            onClick={() => setAutoRefresh(!autoRefresh)}
            disabled={!isConnected}
          >
            <Zap className="h-4 w-4 mr-1" />
            Auto
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
        </div>
      </div>

      {/* Opportunities Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {processedOpportunities.map((opportunity, index) => (
          <Card key={`${opportunity.game_id}-${opportunity.market}-${index}`} 
                className="hover:shadow-lg transition-shadow border-l-4 border-l-green-500">
            <CardHeader className="pb-3">
              <div className="flex justify-between items-start">
                <div className="space-y-1">
                  <Badge className={getRecommendationColor(opportunity.recommendation)}>
                    {opportunity.recommendation.replace('_', ' ')}
                  </Badge>
                  <div className="text-sm font-medium">
                    {opportunity.game_info}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {opportunity.current_score} • Q{opportunity.quarter}
                  </div>
                </div>
                <div className="text-right">
                  <div className={`text-lg font-bold ${getEVColor(opportunity.expected_value)}`}>
                    +{(opportunity.expected_value * 100).toFixed(1)}%
                  </div>
                  <div className="text-xs text-muted-foreground">Expected Value</div>
                </div>
              </div>
            </CardHeader>
            
            <CardContent className="space-y-4">
              {/* Bet Details */}
              <div className="bg-muted/50 rounded-lg p-3 space-y-2">
                <div className="flex justify-between items-center">
                  <span className="font-medium">{formatMarket(opportunity.market)}</span>
                  <span className="text-sm text-muted-foreground">{opportunity.bookmaker}</span>
                </div>
                
                {opportunity.line && (
                  <div className="flex justify-between">
                    <span className="text-sm">Line:</span>
                    <span className="text-sm font-medium">{opportunity.line}</span>
                  </div>
                )}
                
                <div className="flex justify-between">
                  <span className="text-sm">Odds:</span>
                  <span className="text-sm font-medium">{formatOdds(opportunity.odds)}</span>
                </div>
              </div>

              {/* Probability Analysis */}
              <div className="space-y-2">
                <h4 className="text-sm font-medium">Probability Analysis</h4>
                <div className="grid grid-cols-2 gap-2 text-xs">
                  <div className="bg-green-50 dark:bg-green-950/20 rounded p-2">
                    <div className="font-medium">Your Model</div>
                    <div className="text-green-700 dark:text-green-400">
                      {(opportunity.your_probability * 100).toFixed(1)}%
                    </div>
                  </div>
                  <div className="bg-gray-50 dark:bg-gray-950/20 rounded p-2">
                    <div className="font-medium">Implied</div>
                    <div className="text-gray-700 dark:text-gray-400">
                      {(opportunity.implied_probability * 100).toFixed(1)}%
                    </div>
                  </div>
                </div>
                
                <div className="flex justify-between items-center text-sm">
                  <span>Edge:</span>
                  <span className="font-medium text-green-600">
                    {((opportunity.your_probability - opportunity.implied_probability) * 100).toFixed(1)}%
                  </span>
                </div>
                
                <div className="flex justify-between items-center text-sm">
                  <span>Confidence:</span>
                  <div className="flex items-center gap-1">
                    <div className="w-16 bg-gray-200 rounded-full h-2">
                      <div 
                        className="bg-blue-600 h-2 rounded-full" 
                        style={{ width: `${(opportunity.confidence || 0) * 100}%` }}
                      ></div>
                    </div>
                    <span className="text-xs">{((opportunity.confidence || 0) * 100).toFixed(0)}%</span>
                  </div>
                </div>
              </div>

              {/* Kelly Sizing */}
              {opportunity.kelly_fraction && (
                <div className="bg-blue-50 dark:bg-blue-950/20 rounded-lg p-3">
                  <div className="flex justify-between items-center">
                    <span className="text-sm font-medium">Kelly Sizing</span>
                    <span className="text-sm font-bold text-blue-700 dark:text-blue-400">
                      {(opportunity.kelly_fraction * 100).toFixed(1)}%
                    </span>
                  </div>
                  {opportunity.suggested_bet_size && (
                    <div className="text-xs text-muted-foreground mt-1">
                      Suggested: {opportunity.suggested_bet_size}
                    </div>
                  )}
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex gap-2 pt-2 border-t">
                <Button variant="outline" size="sm" className="flex-1">
                  <Brain className="h-3 w-3 mr-1" />
                  Details
                </Button>
                <Button 
                  variant="default" 
                  size="sm" 
                  className="flex-1"
                  disabled={opportunity.expected_value < 0.03}
                >
                  <Target className="h-3 w-3 mr-1" />
                  Place Bet
                </Button>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Empty State */}
      {processedOpportunities.length === 0 && (
        <Card className="text-center py-12">
          <CardContent>
            <Target className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
            <h3 className="text-lg font-medium mb-2">No opportunities found</h3>
            <p className="text-muted-foreground mb-4">
              {filterBy === 'all' 
                ? 'No profitable betting opportunities detected at the moment.' 
                : `No ${filterBy.replace('_', ' ')} opportunities available.`
              }
            </p>
            {!isConnected && (
              <Alert className="max-w-md mx-auto mb-4">
                <AlertTriangle className="h-4 w-4" />
                <AlertDescription>
                  Real-time connection required for live opportunities
                </AlertDescription>
              </Alert>
            )}
            <Button onClick={refreshOpportunities} disabled={!isConnected}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh Opportunities
            </Button>
          </CardContent>
        </Card>
      )}

      {/* Auto-refresh indicator */}
      {autoRefresh && isConnected && processedOpportunities.length > 0 && (
        <div className="text-center">
          <Badge variant="outline" className="text-xs">
            <Zap className="h-3 w-3 mr-1" />
            Auto-refreshing every 15 seconds
          </Badge>
        </div>
      )}
    </div>
  );
};

export default LiveOpportunities;
