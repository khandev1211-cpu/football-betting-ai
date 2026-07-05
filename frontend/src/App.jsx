import React, { useState, useEffect } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { 
  BarChart3, 
  Table, 
  Settings, 
  AlertCircle,
  Wifi,
  WifiOff,
  Activity
} from 'lucide-react';
import Dashboard from './components/Dashboard';
import OddsTable from './components/OddsTable';
import UpcomingMatches from './components/UpcomingMatches';
import LiveMatches from './components/LiveMatches';
import LiveOpportunities from './components/LiveOpportunities';
import ESPNScoreboard from './components/ESPNScoreboard';
import { api } from '@/lib/api';
import './App.css';

function App() {
  const [upcomingGames, setUpcomingGames] = useState([]);
  const [liveGames, setLiveGames] = useState([]);
  const [oddsData, setOddsData] = useState([]);
  const [scoreboardData, setScoreboardData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');
  const [lastUpdate, setLastUpdate] = useState(null);

  // Check backend connection
  const checkBackendHealth = async () => {
    try {
      console.log('Checking backend health...');
      const response = await fetch('/api/health', { timeout: 5000 });
      console.log('Health check response:', response.status, response.ok);
      if (response.ok) {
        setConnectionStatus('connected');
        console.log('Backend connected successfully');
        return true;
      } else {
        setConnectionStatus('disconnected');
        setError('Backend health check failed');
        console.log('Backend health check failed:', response.status);
        return false;
      }
    } catch (err) {
      setConnectionStatus('disconnected');
      setError('Cannot connect to backend server');
      console.log('Backend connection error:', err);
      return false;
    }
  };

  // Fetch upcoming games with predictions (including NCAAF)
  const fetchUpcomingGames = async () => {
    try {
      console.log('fetchUpcomingGames called - attempting ESPN API...');
      // Fetch ESPN data which includes both NFL and NCAAF
      const espnResult = await api.espn.getScoreboard({ days: 10 });
      
      console.log('ESPN API response:', espnResult);
      console.log('ESPN API success:', espnResult.success);
      console.log('ESPN API data exists:', !!espnResult.data);
      
      if (espnResult.success && espnResult.data) {
        // Combine NFL and NCAAF upcoming games
        const nflGames = espnResult.data.upcoming?.nfl || [];
        const ncaafGames = espnResult.data.upcoming?.ncaaf || [];
        const allUpcomingGames = [...nflGames, ...ncaafGames];
        
        console.log('fetchUpcomingGames - ESPN API SUCCESS:');
        console.log('NFL games:', nflGames.length);
        console.log('NCAAF games:', ncaafGames.length);
        console.log('Combined games:', allUpcomingGames.length);
        console.log('First 3 combined games:', allUpcomingGames.slice(0, 3).map(g => ({
          teams: `${g.away_team} @ ${g.home_team}`,
          sport_key: g.sport_key
        })));
        
        setUpcomingGames(allUpcomingGames);
        setScoreboardData(espnResult.data);
        return allUpcomingGames;
      } else {
        console.log('ESPN API failed or returned no data, falling back to original API');
        console.log('ESPN result:', espnResult);
        
        // TEMPORARY: Force use ESPN data even if success is false
        if (espnResult.data && espnResult.data.upcoming) {
          console.log('FORCING ESPN DATA USAGE despite success=false');
          const nflGames = espnResult.data.upcoming?.nfl || [];
          const ncaafGames = espnResult.data.upcoming?.ncaaf || [];
          const allUpcomingGames = [...nflGames, ...ncaafGames];
          
          console.log('FORCED ESPN DATA:');
          console.log('NFL games:', nflGames.length);
          console.log('NCAAF games:', ncaafGames.length);
          console.log('Combined games:', allUpcomingGames.length);
          
          setUpcomingGames(allUpcomingGames);
          setScoreboardData(espnResult.data);
          return allUpcomingGames;
        }
        
        // Fallback to original API
        const result = await api.getUpcomingGames({
          include_predictions: 'true',
          days: '10'
        });
        
        console.log('Fallback API result:', result);
        
        if (result.success) {
          setUpcomingGames(result.data);
          return result.data;
        } else {
          throw new Error(result.error || 'Failed to fetch upcoming games');
        }
      }
    } catch (err) {
      console.error('Error fetching upcoming games:', err);
      console.log('Attempting fallback to original API due to error...');
      
      try {
        const result = await api.getUpcomingGames({
          include_predictions: 'true',
          days: '10'
        });
        
        if (result.success) {
          console.log('Fallback API successful:', result.data?.length, 'games');
          setUpcomingGames(result.data);
          return result.data;
        }
      } catch (fallbackErr) {
        console.error('Fallback API also failed:', fallbackErr);
      }
    }
  };

  // Fetch live games
  const fetchLiveGames = async () => {
    try {
      const result = await api.getLiveGames({
        sport: 'nfl',
        include_odds: 'true'
      });
      
      if (result.success) {
        setLiveGames(result.data);
        return result.data;
      } else {
        throw new Error(result.error || 'Failed to fetch live games');
      }
    } catch (err) {
      console.error('Error fetching live games:', err);
      throw err;
    }
  };

  // Fetch odds data
  const fetchOdds = async () => {
    try {
      // Fetch both NFL and NCAAF odds
      const [nflResult, ncaafResult] = await Promise.all([
        api.getOdds({
          sport: 'nfl',
          best_only: 'true'
        }),
        api.getOdds({
          sport: 'ncaaf',
          best_only: 'true'
        })
      ]);
      
      // Combine both datasets
      const combinedData = [];
      if (nflResult.success) {
        combinedData.push(...nflResult.data);
      }
      if (ncaafResult.success) {
        combinedData.push(...ncaafResult.data);
      }
      
      const result = {
        success: combinedData.length > 0,
        data: combinedData
      };
      
      if (result.success) {
        setOddsData(result.data);
        return result.data;
      } else {
        throw new Error(result.error || 'Failed to fetch odds');
      }
    } catch (err) {
      console.error('Error fetching odds:', err);
      throw err;
    }
  };

  // Refresh all data
  const refreshData = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      console.log('refreshData called - fetching fresh data...');
      const upcomingData = await fetchUpcomingGames();
      console.log('refreshData - upcoming games fetched:', upcomingData?.length);
      console.log('refreshData - first 3 games:', upcomingData?.slice(0, 3).map(g => ({
        teams: `${g.away_team} @ ${g.home_team}`,
        sport_key: g.sport_key
      })));
      
      await Promise.all([
        fetchLiveGames(),
        fetchOdds()
      ]);
      setLastUpdate(new Date());
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  // Initial data load
  useEffect(() => {
    console.log('App useEffect - initial data load');
    
    // Check backend health first
    checkBackendHealth().then(() => {
      // Force immediate refresh to trigger ESPN API
      setTimeout(() => {
        console.log('Forcing data refresh...');
        refreshData();
      }, 100);
    });
    
    // Set up periodic refresh (every 5 minutes)
    const interval = setInterval(refreshData, 5 * 60 * 1000);
    
    return () => clearInterval(interval);
  }, []);

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected': return 'text-green-500';
      case 'disconnected': return 'text-red-500';
      case 'error': return 'text-yellow-500';
      default: return 'text-gray-500';
    }
  };

  const getConnectionIcon = () => {
    switch (connectionStatus) {
      case 'connected': return <Wifi className="h-4 w-4" />;
      case 'disconnected': return <WifiOff className="h-4 w-4" />;
      case 'error': return <AlertCircle className="h-4 w-4" />;
      default: return <Activity className="h-4 w-4" />;
    }
  };

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="border-b bg-card">
        <div className="container mx-auto px-4 py-4">
          <div className="flex justify-between items-center">
            <div className="flex items-center space-x-4">
              <div className="flex items-center space-x-2">
                <BarChart3 className="h-8 w-8 text-primary" />
                <div>
                  <h1 className="text-2xl font-bold">Football Betting AI</h1>
                  <p className="text-sm text-muted-foreground">
                    AI-Powered Prediction & EV Analysis
                  </p>
                </div>
              </div>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Connection Status */}
              <div className="flex items-center space-x-2">
                <div className={`flex items-center space-x-1 ${getConnectionStatusColor()}`}>
                  {getConnectionIcon()}
                  <span className="text-sm capitalize">{connectionStatus}</span>
                </div>
                {lastUpdate && (
                  <div className="text-xs text-muted-foreground">
                    Last update: {lastUpdate.toLocaleTimeString()}
                  </div>
                )}
              </div>
              
              {/* Data Stats */}
              <div className="flex items-center space-x-2">
                <Badge variant="outline">
                  {upcomingGames.length} Upcoming
                </Badge>
                <Badge variant="outline">
                  0 Live
                </Badge>
                <Badge variant="outline">
                  {oddsData.length} Odds
                </Badge>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {/* Error Alert */}
        {error && (
          <Alert className="mb-6" variant="destructive">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              {error}
              <Button 
                variant="outline" 
                size="sm" 
                className="ml-2"
                onClick={refreshData}
              >
                Retry
              </Button>
            </AlertDescription>
          </Alert>
        )}

        {/* Main Tabs */}
        <Tabs defaultValue="dashboard" className="space-y-6">
          <TabsList className="grid w-full grid-cols-7">
            <TabsTrigger value="dashboard" className="flex items-center gap-2">
              <BarChart3 className="h-4 w-4" />
              Dashboard
            </TabsTrigger>
            <TabsTrigger value="scoreboard" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Scoreboard
            </TabsTrigger>
            <TabsTrigger value="upcoming" className="flex items-center gap-2">
              <Activity className="h-4 w-4" />
              Upcoming
            </TabsTrigger>
            <TabsTrigger value="live" className="flex items-center gap-2">
              <Wifi className="h-4 w-4" />
              Live
            </TabsTrigger>
            <TabsTrigger value="opportunities" className="flex items-center gap-2">
              <AlertCircle className="h-4 w-4" />
              Opportunities
            </TabsTrigger>
            <TabsTrigger value="odds" className="flex items-center gap-2">
              <Table className="h-4 w-4" />
              Odds
            </TabsTrigger>
            <TabsTrigger value="settings" className="flex items-center gap-2">
              <Settings className="h-4 w-4" />
              Settings
            </TabsTrigger>
          </TabsList>

          <TabsContent value="dashboard">
            <Dashboard 
              upcomingGames={upcomingGames}
              liveGames={liveGames}
              onRefresh={refreshData}
              isLoading={isLoading}
            />
          </TabsContent>

          <TabsContent value="scoreboard">
            <ESPNScoreboard 
              scoreboardData={scoreboardData}
              onRefresh={refreshData}
              isLoading={isLoading}
            />
          </TabsContent>

          <TabsContent value="upcoming">
            <UpcomingMatches 
              games={upcomingGames}
              onRefresh={refreshData}
              isLoading={isLoading}
            />
          </TabsContent>

          <TabsContent value="live">
            <LiveMatches 
              onRefresh={refreshData}
              isLoading={isLoading}
            />
          </TabsContent>

          <TabsContent value="opportunities">
            <LiveOpportunities 
              onRefresh={refreshData}
              isLoading={isLoading}
            />
          </TabsContent>

          <TabsContent value="odds">
            <OddsTable 
              games={oddsData}
              onRefresh={refreshData}
              isLoading={isLoading}
            />
          </TabsContent>

          <TabsContent value="settings">
            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Application Settings</CardTitle>
                  <CardDescription>
                    Configure your betting analysis preferences
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <div>
                      <h3 className="text-lg font-medium mb-3">API Configuration</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Odds API Status:</span>
                          <Badge variant={connectionStatus === 'connected' ? 'default' : 'destructive'}>
                            {connectionStatus}
                          </Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Model Status:</span>
                          <Badge variant="default">Loaded</Badge>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Auto Refresh:</span>
                          <Badge variant="outline">5 minutes</Badge>
                        </div>
                      </div>
                    </div>
                    
                    <div>
                      <h3 className="text-lg font-medium mb-3">Betting Preferences</h3>
                      <div className="space-y-3">
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Default Bankroll:</span>
                          <span className="text-sm font-medium">$1,000</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Min EV Threshold:</span>
                          <span className="text-sm font-medium">2%</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <span className="text-sm">Kelly Fraction:</span>
                          <span className="text-sm font-medium">25%</span>
                        </div>
                      </div>
                    </div>
                  </div>
                  
                  <div className="pt-4 border-t">
                    <h3 className="text-lg font-medium mb-3">System Information</h3>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="text-muted-foreground">Version:</span>
                        <div className="font-medium">1.0.0</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Model:</span>
                        <div className="font-medium">NFL LightGBM</div>
                      </div>
                      <div>
                        <span className="text-muted-foreground">Last Update:</span>
                        <div className="font-medium">
                          {lastUpdate ? lastUpdate.toLocaleString() : 'Never'}
                        </div>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>About</CardTitle>
                  <CardDescription>
                    Football Betting AI Prediction System
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-4 text-sm">
                    <p>
                      This application provides AI-powered predictions and Expected Value (EV) calculations 
                      for NFL and College Football betting. It uses machine learning models to analyze 
                      team performance, historical data, and current odds to identify profitable betting opportunities.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <h4 className="font-medium mb-2">Features:</h4>
                        <ul className="space-y-1 text-muted-foreground">
                          <li>• Real-time odds fetching</li>
                          <li>• AI-powered predictions</li>
                          <li>• Expected Value calculations</li>
                          <li>• Kelly Criterion bet sizing</li>
                          <li>• Interactive dashboard</li>
                        </ul>
                      </div>
                      <div>
                        <h4 className="font-medium mb-2">Supported Markets:</h4>
                        <ul className="space-y-1 text-muted-foreground">
                          <li>• Moneyline bets</li>
                          <li>• Point spreads</li>
                          <li>• Over/Under totals</li>
                          <li>• NFL & NCAAF</li>
                        </ul>
                      </div>
                    </div>
                    <div className="pt-4 border-t">
                      <p className="text-xs text-muted-foreground">
                        <strong>Disclaimer:</strong> This system is for educational purposes only. 
                        Please ensure compliance with local gambling laws and bet responsibly.
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}

export default App;

