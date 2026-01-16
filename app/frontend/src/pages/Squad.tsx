import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { SquadRow } from "@/components/SquadRow";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { PlayerInfoRibbon } from "@/components/PlayerInfoRibbon";
import { FootballerInfoDialog } from "@/components/FootballerInfoDialog";
import { fetchSquadFootballers, Footballer } from "@/lib/api";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { useAuth } from "@/contexts/AuthContext";

// Sample placeholder data for visualization
const sampleFootballers: Footballer[] = [
  { id: 45, name: "Luka Modrić", team: "Real Madrid", value: 25000000, totalPoints: 75, averagePoints: 7.5, onMarket: false, onMarketSince: null },
  { id: 78, name: "Kevin De Bruyne", team: "Man City", value: 45000000, totalPoints: 41, averagePoints: 7.5, onMarket: true, onMarketSince: "2025-11-05T14:30:00+00:00" },
  { id: 122, name: "Robert Lewandowski", team: "Barcelona", value: 38000000, totalPoints: 256, averagePoints: 7.5, onMarket: false, onMarketSince: null },
  { id: 89, name: "Thibaut Courtois", team: "Real Madrid", value: 22000000, totalPoints: 1, averagePoints: 4.5, onMarket: false, onMarketSince: null },
  { id: 156, name: "João Cancelo", team: "Barcelona", value: 18000000, totalPoints: 38, averagePoints: 7.5, onMarket: true, onMarketSince: "2025-11-07T09:15:00+00:00" },
  { id: 201, name: "Pedri", team: "Barcelona", value: 35000000, totalPoints: 13, averagePoints: 7.5, onMarket: false, onMarketSince: null },
  { id: 67, name: "Frenkie de Jong", team: "Barcelona", value: 32000000, totalPoints: 75, averagePoints: 7.5, onMarket: false, onMarketSince: null },
  { id: 143, name: "Vinícius Júnior", team: "Real Madrid", value: 55000000, totalPoints: 43, averagePoints: 0.5, onMarket: true, onMarketSince: "2025-11-08T16:45:00+00:00" },
  { id: 98, name: "Marc-André ter Stegen", team: "Barcelona", value: 24000000, totalPoints: 75, averagePoints: 7.51, onMarket: false, onMarketSince: null },
  { id: 234, name: "Rodri", team: "Man City", value: 42000000, totalPoints: 75, averagePoints: 7.5, onMarket: false, onMarketSince: null },
  { id: 176, name: "Gavi", team: "Barcelona", value: 28000000, totalPoints: 1, averagePoints: 3.54, onMarket: false, onMarketSince: null },
];

const Squad = () => {
  const { playerId } = useParams();
  const { user } = useAuth();
  const [footballers, setFootballers] = useState<Footballer[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFootballer, setSelectedFootballer] = useState<Footballer | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  
  useEffect(() => {
    const loadFootballers = async () => {
      setLoading(true);
      try {
        // Use playerId from URL params or default to logged-in user
        const id = playerId || user?.playerId?.toString() || localStorage.getItem("playerId");
        const data = await fetchSquadFootballers(id);
        setFootballers(data);
      } catch (error) {
        console.log('Failed to fetch squad data, using sample data for visualization');
        // Use sample data when API is not available
        setFootballers(sampleFootballers);
      } finally {
        setLoading(false);
      }
    };
    
    loadFootballers();
  }, [playerId, user?.playerId]);

  const handleFootballerClick = (footballer: Footballer) => {
    setSelectedFootballer(footballer);
    setDialogOpen(true);
  };
  
  return (
    <div className="min-h-screen bg-background pb-20">
      <Header showBackButton />
      <NavigationTabs />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <LoadingSkeleton type="footballers" />
        ) : (
          <div className="max-w-4xl">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Player</TableHead>
                  <TableHead className="text-center">Total points</TableHead>
                  <TableHead className="text-center">Average points</TableHead>
                  <TableHead className="text-center">Value</TableHead>
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
        )}
      </main>
      
      {selectedFootballer && (
        <FootballerInfoDialog
          open={dialogOpen}
          onOpenChange={setDialogOpen}
          footballerId={selectedFootballer.id}
          footballerName={selectedFootballer.name}
        />
      )}
      
      <PlayerInfoRibbon />
    </div>
  );
};

export default Squad;
