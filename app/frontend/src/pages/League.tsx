import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { PlayerRow } from "@/components/PlayerRow";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { PlayerInfoRibbon } from "@/components/PlayerInfoRibbon";
import { SquadRow } from "@/components/SquadRow";
import { FootballerInfoDialog } from "@/components/FootballerInfoDialog";
import { 
  fetchLeaderboard, 
  fetchOpenedFixtures, 
  fetchPlayerFixtures,
  fetchSquadFootballers,
  fetchFixtureLineup,
  fetchFootballerShortName,
  fetchFootballerFixturePoints,
  Player,
  Footballer 
} from "@/lib/api";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowLeft, Loader2 } from "lucide-react";

const API_ENDPOINT = import.meta.env.VITE_BACKEND_URL;

const League = () => {
  const { leagueId } = useParams();
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  const [fixtures, setFixtures] = useState<number[]>([]);
  const [selectedFixture, setSelectedFixture] = useState<string>("total");
  const [selectedPlayerId, setSelectedPlayerId] = useState<number | null>(null);
  const [selectedPlayerName, setSelectedPlayerName] = useState<string>("");
  
  // Squad view state (for "total")
  const [footballers, setFootballers] = useState<Footballer[]>([]);
  const [selectedFootballer, setSelectedFootballer] = useState<Footballer | null>(null);
  const [squadDialogOpen, setSquadDialogOpen] = useState(false);
  
  // Fixture view state (for specific fixture)
  const [formation, setFormation] = useState<number[]>([]);
  const [lineupFootballers, setLineupFootballers] = useState<number[][]>([]);
  const [footballerNames, setFootballerNames] = useState<Record<number, string>>({});
  const [footballerPoints, setFootballerPoints] = useState<Record<number, number | null>>({});
  const [selectedFootballerId, setSelectedFootballerId] = useState<number | null>(null);
  const [fixtureDialogOpen, setFixtureDialogOpen] = useState(false);
  
  // Fetch available fixtures depending on selected player
  useEffect(() => {
    const loadFixtures = async () => {
      try {
        if (selectedPlayerId === null) {
          const data = await fetchOpenedFixtures();
          setFixtures(data);
        } else {
          const data = await fetchPlayerFixtures(selectedPlayerId.toString());
          setFixtures(data);
        }
      } catch (error) {
        console.log('Failed to fetch fixtures');
      }
    };
    loadFixtures();
  }, [selectedPlayerId]);

  // Fetch leaderboard when selectedFixture changes or when returning to leaderboard view
  useEffect(() => {
    if (selectedPlayerId === null) {
      const loadPlayers = async () => {
        setLoading(true);
        try {
          const data = await fetchLeaderboard(selectedFixture);
          setPlayers(data);
        } catch (error) {
          console.error('Failed to fetch leaderboard data:', error);
          setPlayers([]);
        } finally {
          setLoading(false);
        }
      };
      
      loadPlayers();
    }
  }, [selectedFixture, selectedPlayerId]);
  
  // Fetch player's squad or fixture when a player is selected
  useEffect(() => {
    if (selectedPlayerId === null) return;
    
    const loadPlayerData = async () => {
      setLoading(true);
      try {
        if (selectedFixture === "total") {
          // Show squad view
          const data = await fetchSquadFootballers(selectedPlayerId.toString());
          setFootballers(data);
        } else {
          // Show fixture view
          const { lineup, lineupFootballers: footballersData } = await fetchFixtureLineup(
            selectedPlayerId.toString(), 
            parseInt(selectedFixture)
          );
          setFormation(lineup);
          setLineupFootballers(footballersData);

          // Fetch short names and points for all footballers
          const allFootballerIds = footballersData.flat().filter(id => id !== undefined);
          const namePromises = allFootballerIds.map(id => 
            fetchFootballerShortName(id).then(name => ({ id, name }))
          );
          const pointsPromises = allFootballerIds.map(id => 
            fetchFootballerFixturePoints(id, parseInt(selectedFixture)).then(points => ({ id, points }))
          );
          
          const [names, points] = await Promise.all([
            Promise.all(namePromises),
            Promise.all(pointsPromises)
          ]);
          
          const namesMap = names.reduce((acc, { id, name }) => {
            acc[id] = name;
            return acc;
          }, {} as Record<number, string>);
          const pointsMap = points.reduce((acc, { id, points }) => {
            acc[id] = points;
            return acc;
          }, {} as Record<number, number | null>);
          
          setFootballerNames(namesMap);
          setFootballerPoints(pointsMap);
        }
      } catch (error) {
        console.error('Failed to fetch player data:', error);
      } finally {
        setLoading(false);
      }
    };
    
    loadPlayerData();
  }, [selectedPlayerId, selectedFixture]);
  const handlePlayerClick = (playerId: number, playerName: string) => {
    setSelectedPlayerId(playerId);
    setSelectedPlayerName(playerName);
    setSelectedFixture("total");
  };
  
  const handleBackToLeaderboard = () => {
    setSelectedPlayerId(null);
    setSelectedPlayerName("");
    setFootballers([]);
    setFormation([]);
    setLineupFootballers([]);
    setFootballerNames({});
    setFootballerPoints({});
    setSelectedFootballer(null);
    setSelectedFootballerId(null);
    setSquadDialogOpen(false);
    setFixtureDialogOpen(false);
  };
  
  const handleFootballerClick = (footballer?: Footballer | number) => {
    if (typeof footballer === "number") {
      // From fixture view
      setSelectedFootballerId(footballer);
      setFixtureDialogOpen(true);
    } else if (footballer) {
      // From squad view
      setSelectedFootballer(footballer);
      setSquadDialogOpen(true);
    }
  };
  
  const renderRow = (count: number, rowIndex: number) => {
    const footballersInRow = lineupFootballers[rowIndex] || [];
    
    return (
      <div className="flex justify-center gap-2 sm:gap-6 w-full" style={{ marginBottom: rowIndex === 0 ? '1.5rem' : '1rem' }}>
        {Array.from({ length: count }).map((_, index) => {
          const footballerId = footballersInRow[index];
          const hasFootballer = footballerId !== undefined;
          const shortName = hasFootballer ? footballerNames[footballerId] : null;
          const points = hasFootballer ? footballerPoints[footballerId] : null;
          
          return (
            <div
              key={`${rowIndex}-${index}`}
              className="flex flex-col items-center gap-0.5 sm:gap-1"
            >
              <div
                className={`relative w-14 h-16 sm:w-24 md:w-32 sm:h-28 md:h-36 bg-card border-2 border-primary rounded-lg flex items-center justify-center transition-colors shadow-lg overflow-hidden ${hasFootballer ? 'hover:bg-primary/10 cursor-pointer' : ''}`}
                onClick={() => hasFootballer && handleFootballerClick(footballerId)}
              >
                {hasFootballer ? (
                  <>
                    <img
                      src={`${API_ENDPOINT}/footballer/image/${footballerId}`}
                      alt="Footballer"
                      className="w-full h-full object-cover"
                    />
                    {/* Points badge - diagonal corner */}
                    {points !== null && (
                      <div className="absolute top-0 right-0 w-8 h-8 sm:w-12 sm:h-12 overflow-hidden">
                        <div
                          className={`absolute top-0 right-0 w-12 h-12 sm:w-16 sm:h-16 transform rotate-45 translate-x-4 sm:translate-x-6 -translate-y-4 sm:-translate-y-6 ${points < 0 ? 'bg-red-600' : 'bg-green-600/60'}`}
                        />
                        <span
                          className={`absolute top-0.5 sm:top-1.5 right-0.5 sm:right-1.5 font-extrabold text-sm sm:text-xl leading-none ${points < 0 ? 'text-red-50' : 'text-green-50'}`}
                        >
                          {points}
                        </span>
                      </div>
                    )}
                  </>
                ) : (
                  <span className="text-[10px] sm:text-sm text-muted-foreground font-medium">Empty</span>
                )}
              </div>
              {shortName && (
                <span className="text-[9px] sm:text-xs font-semibold text-white drop-shadow-md text-center max-w-[56px] sm:max-w-none truncate">
                  {shortName}
                </span>
              )}
            </div>
          );
        })}
      </div>
    );
  };
  
  return (
    <div className="min-h-screen bg-background pb-20">
      <Header showBackButton />
      <NavigationTabs leagueId={leagueId} />
      
      <main className="container mx-auto px-2 sm:px-6 lg:px-8 py-4 sm:py-8">
        <div className="max-w-4xl mb-4 flex flex-wrap items-center gap-2 sm:gap-4">
          {selectedPlayerId !== null && (
            <Button 
              variant="outline" 
              size="sm"
              onClick={handleBackToLeaderboard}
              className="flex items-center gap-2"
            >
              <ArrowLeft className="h-4 w-4" />
              Back
            </Button>
          )}
          <Select value={selectedFixture} onValueChange={setSelectedFixture}>
            <SelectTrigger className="w-[140px] sm:w-[180px]">
              <SelectValue placeholder="Select fixture" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="total">Total</SelectItem>
              {fixtures.map((fixture) => (
                <SelectItem key={fixture} value={fixture.toString()}>
                  J {fixture}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {selectedPlayerId !== null && (
            <h2 className="text-lg sm:text-xl font-semibold">{selectedPlayerName}</h2>
          )}
        </div>
        {loading ? (
          (() => {
            if (selectedPlayerId === null) return <LoadingSkeleton type="players" />;
            if (selectedFixture === "total") return <LoadingSkeleton type="footballers" />;
            return <LoadingSkeleton type="players" />;
          })()
        ) : selectedPlayerId === null ? (
          // Leaderboard view
          <div className="max-w-4xl overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Player</TableHead>
                  <TableHead className="text-center">Points</TableHead>
                  <TableHead className="text-center hidden sm:table-cell">Team Value</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {players.map((player) => (
                  <PlayerRow
                    key={player.id}
                    playerId={player.id}
                    name={player.name}
                    points={player.points}
                    team_value={player.team_value}
                    onPlayerClick={handlePlayerClick}
                  />
                ))}
              </TableBody>
            </Table>
          </div>
        ) : selectedFixture === "total" ? (
          // Squad view for selected player
          <div className="max-w-4xl overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Player</TableHead>
                  <TableHead className="text-center">Total pts</TableHead>
                  <TableHead className="text-center hidden sm:table-cell">Avg pts</TableHead>
                  <TableHead className="text-center hidden sm:table-cell">Value</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {footballers.map((footballer) => (
                  <SquadRow
                    key={footballer.id}
                    id={footballer.id}
                    name={footballer.name}
                    value={footballer.value}
                    totalPoints={footballer.totalPoints}
                    averagePoints={footballer.averagePoints}
                    onClick={() => handleFootballerClick(footballer)}
                  />
                ))}
              </TableBody>
            </Table>
          </div>
        ) : (
          // Fixture view for selected player
          <div className="max-w-4xl mx-auto">
            {formation.length === 0 ? (
              <div className="text-center py-12 text-muted-foreground">
                No lineup data available for this fixture
              </div>
            ) : (
              <Card className="overflow-hidden">
                <CardContent className="p-0">
                  <div 
                    className="relative w-full bg-gradient-to-b from-green-600 to-green-700 p-3 sm:p-8"
                    style={{ aspectRatio: '3/4' }}
                  >
                    {/* Pitch markings */}
                    <div className="absolute inset-2 sm:inset-4 border-2 border-white/40 rounded-lg">
                      {/* Center circle */}
                      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-12 sm:w-24 h-12 sm:h-24 border-2 border-white/40 rounded-full" />
                      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-1.5 sm:w-2 h-1.5 sm:h-2 bg-white/40 rounded-full" />
                      
                      {/* Center line */}
                      <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-white/40" />
                      
                      {/* Goal areas */}
                      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-16 sm:w-32 h-6 sm:h-12 border-2 border-white/40 border-t-0" />
                      <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-16 sm:w-32 h-6 sm:h-12 border-2 border-white/40 border-b-0" />
                    </div>

                    {/* Player positions */}
                    <div className="relative h-full flex flex-col justify-between py-4 sm:py-8">
                      {/* Top row (Attack) */}
                      {formation[2] && renderRow(formation[2], 3)}
                      
                      {/* Second row (Midfield upper) */}
                      {formation[1] && renderRow(formation[1], 2)}
                      
                      {/* Third row (Midfield lower / Defense) */}
                      {formation[0] && renderRow(formation[0], 1)}
                      
                      {/* Bottom row (Goalkeeper) */}
                      {renderRow(1, 0)}
                    </div>
                  </div>
                </CardContent>
              </Card>
            )}
          </div>
        )}
      </main>
      
      {selectedFootballer && (
        <FootballerInfoDialog
          open={squadDialogOpen}
          onOpenChange={setSquadDialogOpen}
          footballerId={selectedFootballer.id}
          footballerName={selectedFootballer.name}
        />
      )}
      
      {selectedFootballerId && (
        <FootballerInfoDialog
          open={fixtureDialogOpen}
          onOpenChange={setFixtureDialogOpen}
          footballerId={selectedFootballerId}
          defaultFixture={selectedFixture !== "total" ? parseInt(selectedFixture) : undefined}
        />
      )}
      
      <PlayerInfoRibbon />
    </div>
  );
};

export default League;
