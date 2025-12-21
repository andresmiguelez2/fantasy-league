import { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { fetchFootballerShortName, fetchOpenedFixtures, fetchFixtureLineup } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Loader2 } from "lucide-react";
import { FootballerInfoDialog } from "@/components/FootballerInfoDialog";

const API_ENDPOINT = import.meta.env.VITE_BACKEND_URL;

const Fixtures = () => {
  const [openedFixtures, setOpenedFixtures] = useState<number[]>([]);
  const [selectedFixture, setSelectedFixture] = useState<number | null>(null);
  const [formation, setFormation] = useState<number[]>([]);
  const [lineupFootballers, setLineupFootballers] = useState<number[][]>([]);
  const [footballerNames, setFootballerNames] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
  const [selectedFootballerId, setSelectedFootballerId] = useState<number | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const playerId = localStorage.getItem("playerId") || "1";

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
        const { lineup, lineupFootballers: footballersData } = await fetchFixtureLineup(playerId, selectedFixture);
        setFormation(lineup);
        setLineupFootballers(footballersData);

        // Fetch short names for all footballers
        const allFootballerIds = footballersData.flat().filter(id => id !== undefined);
        const namePromises = allFootballerIds.map(id => 
          fetchFootballerShortName(id).then(name => ({ id, name }))
        );
        const names = await Promise.all(namePromises);
        const namesMap = names.reduce((acc, { id, name }) => {
          acc[id] = name;
          return acc;
        }, {} as Record<number, string>);
        setFootballerNames(namesMap);
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
      <div className="flex justify-center gap-6 w-full" style={{ marginBottom: rowIndex === 0 ? '3rem' : '2rem' }}>
        {Array.from({ length: count }).map((_, index) => {
          const footballerId = footballersInRow[index];
          const hasFootballer = footballerId !== undefined;
          const shortName = hasFootballer ? footballerNames[footballerId] : null;
          
          return (
            <div
              key={`${rowIndex}-${index}`}
              className="flex flex-col items-center gap-1"
            >
              <div
                className={`w-32 h-36 bg-card border-2 border-primary rounded-lg flex items-center justify-center transition-colors shadow-lg overflow-hidden ${hasFootballer ? 'hover:bg-primary/10 cursor-pointer' : ''}`}
                onClick={() => handleFootballerClick(footballerId)}
              >
                {hasFootballer ? (
                  <img
                    src={`${API_ENDPOINT}/footballer/image/${footballerId}`}
                    alt="Footballer"
                    className="w-full h-full object-cover"
                  />
                ) : (
                  <span className="text-sm text-muted-foreground font-medium">Empty</span>
                )}
              </div>
              {shortName && (
                <span className="text-xs font-semibold text-white drop-shadow-md">
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
      <NavigationTabs />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Fixture Selector Ribbon */}
          <div className="flex gap-2 mb-6 overflow-x-auto pb-2">
            {openedFixtures.map((fixture) => (
              <Button
                key={fixture}
                variant={selectedFixture === fixture ? "default" : "outline"}
                onClick={() => setSelectedFixture(fixture)}
                className="min-w-[4rem]"
              >
                {fixture}
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
                  className="relative w-full bg-gradient-to-b from-green-600 to-green-700 p-8"
                  style={{ aspectRatio: '3/4' }}
                >
                  {/* Pitch markings */}
                  <div className="absolute inset-4 border-2 border-white/40 rounded-lg">
                    {/* Center circle */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 border-2 border-white/40 rounded-full" />
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-white/40 rounded-full" />
                    
                    {/* Center line */}
                    <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-white/40" />
                    
                    {/* Goal areas */}
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-12 border-2 border-white/40 border-t-0" />
                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-32 h-12 border-2 border-white/40 border-b-0" />
                  </div>

                  {/* Player positions */}
                  <div className="relative h-full flex flex-col justify-between py-8">
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
    </div>
  );
};

export default Fixtures;
