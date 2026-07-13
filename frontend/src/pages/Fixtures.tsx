import { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { fetchFootballerShortName, fetchOpenedFixtures, fetchFixtureLineup, fetchFootballerFixturePoints, BACKEND_URL } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { FootballerInfoDialog } from "@/components/FootballerInfoDialog";
import { getActiveLeagueId, getActivePlayerId } from "@/lib/api";
import { PlayerInfoRibbon } from "@/components/PlayerInfoRibbon";

const API_ENDPOINT = BACKEND_URL;

const Fixtures = () => {
  const [openedFixtures, setOpenedFixtures] = useState<number[]>([]);
  const [selectedFixture, setSelectedFixture] = useState<number | null>(null);
  const [formation, setFormation] = useState<number[]>([]);
  const [lineupFootballers, setLineupFootballers] = useState<number[][]>([]);
  const [footballerNames, setFootballerNames] = useState<Record<number, string>>({});
  const [footballerPoints, setFootballerPoints] = useState<Record<number, number | null>>({});
  const [loading, setLoading] = useState(true);
  const [selectedFootballerId, setSelectedFootballerId] = useState<number | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const playerId = getActivePlayerId();
  const leagueId = getActiveLeagueId();

  // Fetch opened fixtures on mount
  useEffect(() => {
    const loadOpenedFixtures = async () => {
      try {
        const fixtures = await fetchOpenedFixtures();
        setOpenedFixtures(fixtures);
        if (fixtures.length > 0) {
          setSelectedFixture(fixtures[fixtures.length - 1]); // Select latest fixture
        }
      } catch (error) {
        console.error("Error fetching opened fixtures:", error);
      }
    };

    loadOpenedFixtures();
  }, []);

  // Fetch lineup when selected fixture changes
  useEffect(() => {
    if (selectedFixture === null) {
      setLoading(false);
      return;
    }

    const loadLineupData = async () => {
      setLoading(true);
      try {
        if (!playerId) {
          setFormation([]);
          setLineupFootballers([]);
          return;
        }

        const { lineup, lineupFootballers: footballersData } = await fetchFixtureLineup(playerId, selectedFixture);
        setFormation(lineup || []);
        setLineupFootballers(footballersData || []);

        // Fetch short names and points for all footballers
        const allFootballerIds = (footballersData || []).flat().filter(id => id !== undefined);
        const namePromises = allFootballerIds.map(id => 
          fetchFootballerShortName(id).then(name => ({ id, name }))
        );
        const pointsPromises = allFootballerIds.map(id => 
          fetchFootballerFixturePoints(id, selectedFixture).then(points => ({ id, points }))
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
      } catch (error) {
        console.error("Error fetching fixture lineup:", error);
        setFormation([]);
        setLineupFootballers([]);
      } finally {
        setLoading(false);
      }
    };

    loadLineupData();
  }, [playerId, selectedFixture]);

  const handleFootballerClick = (footballerId?: number) => {
    if (footballerId) {
      setSelectedFootballerId(footballerId);
      setDialogOpen(true);
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
                onClick={() => handleFootballerClick(footballerId)}
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
                          className={`absolute top-0 right-0 w-12 h-12 sm:w-16 sm:h-16 transform rotate-45 translate-x-4 sm:translate-x-6 -translate-y-4 sm:-translate-y-6 ${points < 0 ? 'bg-red-600' : points === 0 ? 'bg-gray-500/70' : 'bg-green-600/60'}`}
                        />
                        <span
                          className={`absolute top-0.5 sm:top-1.5 right-0.5 sm:right-1.5 font-extrabold text-sm sm:text-xl leading-none ${points < 0 ? 'text-red-50' : points === 0 ? 'text-gray-50' : 'text-green-50'}`}
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
    <div className="min-h-screen bg-background">
      <Header />
      <NavigationTabs leagueId={leagueId} />
      
      <main className="container mx-auto px-2 sm:px-6 lg:px-8 py-4 sm:py-8">
        <div className="max-w-4xl mx-auto">
          {/* Fixture Selector Ribbon */}
          <div className="flex gap-1.5 sm:gap-2 mb-4 sm:mb-6 overflow-x-auto pb-2 scrollbar-hide">
            {openedFixtures.map((fixture) => (
              <Button
                key={fixture}
                variant={selectedFixture === fixture ? "default" : "outline"}
                onClick={() => setSelectedFixture(fixture)}
                className="min-w-[3rem] sm:min-w-[4rem] text-xs sm:text-sm px-2 sm:px-4 flex-shrink-0"
              >
                {`J ${fixture}`}
              </Button>
            ))}
          </div>

          {loading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : formation.length === 0 ? (
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
      </main>

      <FootballerInfoDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        footballerId={selectedFootballerId}
        defaultFixture={selectedFixture}
      />

      <PlayerInfoRibbon />
    </div>
  );
};

export default Fixtures;
