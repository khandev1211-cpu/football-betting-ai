import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  RefreshCw, 
  Search, 
  Filter,
  TrendingUp,
  TrendingDown,
  Clock,
  DollarSign
} from 'lucide-react';

const OddsTable = ({ games, onRefresh, isLoading }) => {
  const [filteredGames, setFilteredGames] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState('commence_time');
  const [filterSport, setFilterSport] = useState('all');
  const [selectedMarket, setSelectedMarket] = useState('moneyline');

  useEffect(() => {
    if (games) {
      let filtered = [...games];

      // Apply search filter
      if (searchTerm) {
        filtered = filtered.filter(game => 
          game.home_team?.toLowerCase().includes(searchTerm.toLowerCase()) ||
          game.away_team?.toLowerCase().includes(searchTerm.toLowerCase())
        );
      }

      // Apply sport filter
      if (filterSport !== 'all') {
        filtered = filtered.filter(game => game.sport_key === filterSport);
      }

      // Apply sorting
      filtered.sort((a, b) => {
        switch (sortBy) {
          case 'commence_time':
            return new Date(a.commence_time) - new Date(b.commence_time);
          case 'home_team':
            return a.home_team?.localeCompare(b.home_team) || 0;
          case 'away_team':
            return a.away_team?.localeCompare(b.away_team) || 0;
          default:
            return 0;
        }
      });

      setFilteredGames(filtered);
    }
  }, [games, searchTerm, sortBy, filterSport]);

  const formatOdds = (odds) => {
    if (!odds || odds === null || odds === undefined) return 'N/A';
    return odds > 0 ? `+${odds}` : `${odds}`;
  };

  const formatDateTime = (dateString) => {
    if (!dateString) return 'TBD';
    const date = new Date(dateString);
    return {
      date: date.toLocaleDateString(),
      time: date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
  };

  const getOddsColor = (odds) => {
    if (!odds) return 'text-muted-foreground';
    return odds > 0 ? 'text-green-600' : 'text-red-600';
  };

  const calculateImpliedProbability = (odds) => {
    if (!odds) return 0;
    if (odds > 0) {
      return (100 / (odds + 100)) * 100;
    } else {
      return (Math.abs(odds) / (Math.abs(odds) + 100)) * 100;
    }
  };

  const renderMoneylineTable = () => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Game</TableHead>
          <TableHead>Date/Time</TableHead>
          <TableHead className="text-center">Home ML</TableHead>
          <TableHead className="text-center">Away ML</TableHead>
          <TableHead className="text-center">Home Prob</TableHead>
          <TableHead className="text-center">Away Prob</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {filteredGames.map((game) => {
          const dateTime = formatDateTime(game.commence_time);
          const homeOdds = game.best_odds?.moneyline?.home;
          const awayOdds = game.best_odds?.moneyline?.away;
          const homeProb = calculateImpliedProbability(homeOdds);
          const awayProb = calculateImpliedProbability(awayOdds);

          return (
            <TableRow key={game.id}>
              <TableCell>
                <div>
                  <div className="font-medium">{game.away_team} @ {game.home_team}</div>
                  <div className="text-sm text-muted-foreground">{game.sport_title}</div>
                </div>
              </TableCell>
              <TableCell>
                <div>
                  <div className="text-sm">{dateTime.date}</div>
                  <div className="text-xs text-muted-foreground">{dateTime.time}</div>
                </div>
              </TableCell>
              <TableCell className="text-center">
                <span className={`font-medium ${getOddsColor(homeOdds)}`}>
                  {formatOdds(homeOdds)}
                </span>
              </TableCell>
              <TableCell className="text-center">
                <span className={`font-medium ${getOddsColor(awayOdds)}`}>
                  {formatOdds(awayOdds)}
                </span>
              </TableCell>
              <TableCell className="text-center">
                <span className="text-sm">{homeProb.toFixed(1)}%</span>
              </TableCell>
              <TableCell className="text-center">
                <span className="text-sm">{awayProb.toFixed(1)}%</span>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );

  const renderSpreadTable = () => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Game</TableHead>
          <TableHead>Date/Time</TableHead>
          <TableHead className="text-center">Spread</TableHead>
          <TableHead className="text-center">Home Spread</TableHead>
          <TableHead className="text-center">Away Spread</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {filteredGames.map((game) => {
          const dateTime = formatDateTime(game.commence_time);
          const spread = game.best_odds?.spread?.line;
          const homeSpreadOdds = game.best_odds?.spread?.home;
          const awaySpreadOdds = game.best_odds?.spread?.away;

          return (
            <TableRow key={game.id}>
              <TableCell>
                <div>
                  <div className="font-medium">{game.away_team} @ {game.home_team}</div>
                  <div className="text-sm text-muted-foreground">{game.sport_title}</div>
                </div>
              </TableCell>
              <TableCell>
                <div>
                  <div className="text-sm">{dateTime.date}</div>
                  <div className="text-xs text-muted-foreground">{dateTime.time}</div>
                </div>
              </TableCell>
              <TableCell className="text-center">
                <span className="font-medium">
                  {spread ? (spread > 0 ? `+${spread}` : spread) : 'N/A'}
                </span>
              </TableCell>
              <TableCell className="text-center">
                <span className={`font-medium ${getOddsColor(homeSpreadOdds)}`}>
                  {formatOdds(homeSpreadOdds)}
                </span>
              </TableCell>
              <TableCell className="text-center">
                <span className={`font-medium ${getOddsColor(awaySpreadOdds)}`}>
                  {formatOdds(awaySpreadOdds)}
                </span>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );

  const renderTotalsTable = () => (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Game</TableHead>
          <TableHead>Date/Time</TableHead>
          <TableHead className="text-center">Total</TableHead>
          <TableHead className="text-center">Over</TableHead>
          <TableHead className="text-center">Under</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {filteredGames.map((game) => {
          const dateTime = formatDateTime(game.commence_time);
          const total = game.best_odds?.totals?.line;
          const overOdds = game.best_odds?.totals?.over;
          const underOdds = game.best_odds?.totals?.under;

          return (
            <TableRow key={game.id}>
              <TableCell>
                <div>
                  <div className="font-medium">{game.away_team} @ {game.home_team}</div>
                  <div className="text-sm text-muted-foreground">{game.sport_title}</div>
                </div>
              </TableCell>
              <TableCell>
                <div>
                  <div className="text-sm">{dateTime.date}</div>
                  <div className="text-xs text-muted-foreground">{dateTime.time}</div>
                </div>
              </TableCell>
              <TableCell className="text-center">
                <span className="font-medium">{total || 'N/A'}</span>
              </TableCell>
              <TableCell className="text-center">
                <span className={`font-medium ${getOddsColor(overOdds)}`}>
                  {formatOdds(overOdds)}
                </span>
              </TableCell>
              <TableCell className="text-center">
                <span className={`font-medium ${getOddsColor(underOdds)}`}>
                  {formatOdds(underOdds)}
                </span>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );

  const getUniqueSeasons = () => {
    if (!games) return [];
    const sports = [...new Set(games.map(game => game.sport_key))];
    return sports;
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold">Live Odds</h2>
          <p className="text-muted-foreground">Real-time betting odds from multiple sportsbooks</p>
        </div>
        <Button onClick={onRefresh} disabled={isLoading} className="flex items-center gap-2">
          <RefreshCw className={`h-4 w-4 ${isLoading ? 'animate-spin' : ''}`} />
          Refresh Odds
        </Button>
      </div>

      {/* Filters */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filters
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Search Teams</label>
              <div className="relative">
                <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Search teams..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="pl-8"
                />
              </div>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Sport</label>
              <Select value={filterSport} onValueChange={setFilterSport}>
                <SelectTrigger>
                  <SelectValue placeholder="Select sport" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Sports</SelectItem>
                  {getUniqueSeasons().map(sport => (
                    <SelectItem key={sport} value={sport}>
                      {sport === 'americanfootball_nfl' ? 'NFL' : 
                       sport === 'americanfootball_ncaaf' ? 'NCAAF' : sport}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Sort By</label>
              <Select value={sortBy} onValueChange={setSortBy}>
                <SelectTrigger>
                  <SelectValue placeholder="Sort by" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="commence_time">Game Time</SelectItem>
                  <SelectItem value="home_team">Home Team</SelectItem>
                  <SelectItem value="away_team">Away Team</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Results</label>
              <div className="text-sm text-muted-foreground pt-2">
                Showing {filteredGames.length} of {games?.length || 0} games
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Odds Tables */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <DollarSign className="h-4 w-4" />
            Betting Odds
          </CardTitle>
          <CardDescription>
            Best odds across all sportsbooks. Odds update in real-time.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={selectedMarket} onValueChange={setSelectedMarket}>
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="moneyline">Moneyline</TabsTrigger>
              <TabsTrigger value="spread">Spread</TabsTrigger>
              <TabsTrigger value="totals">Totals</TabsTrigger>
            </TabsList>

            <TabsContent value="moneyline" className="mt-6">
              {filteredGames.length > 0 ? (
                <div className="rounded-md border">
                  {renderMoneylineTable()}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No games found matching your filters
                </div>
              )}
            </TabsContent>

            <TabsContent value="spread" className="mt-6">
              {filteredGames.length > 0 ? (
                <div className="rounded-md border">
                  {renderSpreadTable()}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No games found matching your filters
                </div>
              )}
            </TabsContent>

            <TabsContent value="totals" className="mt-6">
              {filteredGames.length > 0 ? (
                <div className="rounded-md border">
                  {renderTotalsTable()}
                </div>
              ) : (
                <div className="text-center py-8 text-muted-foreground">
                  No games found matching your filters
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* Summary Stats */}
      {filteredGames.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Games</CardTitle>
              <Clock className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{filteredGames.length}</div>
              <p className="text-xs text-muted-foreground">
                Available for betting
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Home Odds</CardTitle>
              <TrendingUp className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(() => {
                  const homeOdds = filteredGames
                    .map(g => g.best_odds?.moneyline?.home)
                    .filter(odds => odds !== null && odds !== undefined);
                  const avg = homeOdds.length > 0 
                    ? homeOdds.reduce((sum, odds) => sum + odds, 0) / homeOdds.length 
                    : 0;
                  return formatOdds(Math.round(avg));
                })()}
              </div>
              <p className="text-xs text-muted-foreground">
                Moneyline average
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg Away Odds</CardTitle>
              <TrendingDown className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {(() => {
                  const awayOdds = filteredGames
                    .map(g => g.best_odds?.moneyline?.away)
                    .filter(odds => odds !== null && odds !== undefined);
                  const avg = awayOdds.length > 0 
                    ? awayOdds.reduce((sum, odds) => sum + odds, 0) / awayOdds.length 
                    : 0;
                  return formatOdds(Math.round(avg));
                })()}
              </div>
              <p className="text-xs text-muted-foreground">
                Moneyline average
              </p>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
};

export default OddsTable;

