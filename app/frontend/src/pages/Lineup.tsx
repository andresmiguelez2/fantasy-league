import { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { fetchLineupFormation, fetchLineupFootballers, fetchFootballerShortName } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";
import { SubstitutesDialog } from "@/components/SubstitutesDialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Button } from "@/components/ui/button";
import { POSSIBLE_FORMATIONS } from "@/lib/constants";
import { useAuth } from "@/contexts/AuthContext";

const API_ENDPOINT = import.meta.env.VITE_BACKEND_URL;

const Lineup = () => {
  const [formation, setFormation] = useState<number[]>([]);
  const [lineupFootballers, setLineupFootballers] = useState<number[][]>([]);
  const [footballerNames, setFootballerNames] = useState<Record<number, string>>({});
  const [loading, setLoading] = useState(true);
const [selectedPosition, setSelectedPosition] = useState<number>(0);
  const [selectedFootballerId, setSelectedFootballerId] = useState<number | undefined>();
  const [dialogOpen, setDialogOpen] = useState(false);
  const { user } = useAuth();
  const playerId = user?.playerId?.toString() || localStorage.getItem("playerId");

  useEffect(() => {
    const loadLineupData = async () => {
      try {
        const [formationData, footballersData] = await Promise.all([
          fetchLineupFormation(playerId),
          fetchLineupFootballers(playerId)
        ]);
        setFormation(formationData);
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
        console.error("Error fetching lineup:", error);
        // Default formation if API fails
        setFormation([4, 4, 2]);
        setLineupFootballers([]);
      } finally {
        setLoading(false);
      }
    };

    loadLineupData();
  }, [playerId]);

const handleFootballerClick = (rowIndex: number, footballerId?: number) => {
    setSelectedPosition(rowIndex);
    setSelectedFootballerId(footballerId);
    setDialogOpen(true);
  };

  const handleSwapComplete = async () => {
    setLoading(true);
    try {
      const [formationData, footballersData] = await Promise.all([
        fetchLineupFormation(playerId),
        fetchLineupFootballers(playerId)
      ]);
      setFormation(formationData);
      setLineupFootballers(footballersData);

      const allFootballerIds = footballersData.flat().filter(id => id !== undefined);
      const namePromises = allFootballerIds.map(id => 
        fetchFootballerShortName(id).then(name => ({ id, name }))
      );
      const names = await Promise.all(namePromises);
      const namesMap = names.reduce((acc, { id, name }) => {
        acc[id] = name;
        return acc;
      }, {} as Record<string, string>);
      setFootballerNames(namesMap);
    } catch (error) {
      console.error("Error refreshing lineup:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleFormationChange = async (newFormation: number[]) => {
    setLoading(true);
    try {
      const response = await fetch(`${API_ENDPOINT}/player/update/lineup/${playerId}`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(newFormation),
      });

      if (!response.ok) {
        throw new Error("Failed to update lineup");
      }

      // Refresh the lineup data
      await handleSwapComplete();
    } catch (error) {
      console.error("Error updating formation:", error);
    } finally {
      setLoading(false);
    }
  };

  const getFormationString = () => {
    return formation.join('-');
  };

  const renderRow = (count: number, rowIndex: number) => {
    const footballersInRow = lineupFootballers[rowIndex] || [];
    
    return (
      <div className="flex justify-center gap-2 sm:gap-6 w-full" style={{ marginBottom: rowIndex === 0 ? '1.5rem' : '1rem' }}>
        {Array.from({ length: count }).map((_, index) => {
          const footballerId = footballersInRow[index];
          const hasFootballer = footballerId !== undefined;
          const shortName = hasFootballer ? footballerNames[footballerId] : null;
          
          return (
            <div
              key={`${rowIndex}-${index}`}
              className="flex flex-col items-center gap-0.5 sm:gap-1"
            >
              <div
                className="w-14 h-16 sm:w-24 md:w-32 sm:h-28 md:h-36 bg-card border-2 border-primary rounded-lg flex items-center justify-center transition-colors shadow-lg overflow-hidden hover:bg-primary/10 cursor-pointer"
                onClick={() => handleFootballerClick(rowIndex, footballerId)}
              >
                {hasFootballer ? (
                  <img
                    src={`${API_ENDPOINT}/footballer/image/${footballerId}`}
                    alt="Footballer"
                    className="w-full h-full object-cover"
                  />
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
      <NavigationTabs />
      
      <main className="container mx-auto px-2 sm:px-6 lg:px-8 py-4 sm:py-8">
        <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-between mb-4 sm:mb-6">
          <h1 className="text-xl sm:text-3xl font-bold"></h1>
          {!loading && formation.length > 0 && (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="default" size="lg" className="font-bold text-base sm:text-lg">
                  {getFormationString()}
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                {POSSIBLE_FORMATIONS.map((form) => (
                  <DropdownMenuItem
                    key={form.join('-')}
                    onClick={() => handleFormationChange(form)}
                  >
                    {form[0]}-{form[1]}-{form[2]}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          )}
        </div>          {loading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
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

      <SubstitutesDialog
        open={dialogOpen}
        onOpenChange={setDialogOpen}
        playerId={playerId}
        position={selectedPosition}
        currentFootballerId={selectedFootballerId}
        onSwapComplete={handleSwapComplete}
      />
    </div>
  );
};

export default Lineup;

