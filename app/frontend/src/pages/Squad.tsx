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

const Squad = () => {
  const { playerId, leagueId } = useParams();
  const { user } = useAuth();
  const [footballers, setFootballers] = useState<Footballer[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedFootballer, setSelectedFootballer] = useState<Footballer | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  
  useEffect(() => {
    const loadFootballers = async () => {
      setLoading(true);
      try {
        const id = playerId || user?.playerId?.toString();
        const data = await fetchSquadFootballers(id, leagueId);
        setFootballers(data);
      } catch (error) {
        console.error('Failed to fetch squad data:', error);
        setFootballers([]);
      } finally {
        setLoading(false);
      }
    };
    
    loadFootballers();
  }, [playerId, leagueId, user?.playerId]);

  const handleFootballerClick = (footballer: Footballer) => {
    setSelectedFootballer(footballer);
    setDialogOpen(true);
  };
  
  return (
    <div className="min-h-screen bg-background pb-20">
      <Header showBackButton />
      <NavigationTabs />
      
      <main className="container mx-auto px-2 sm:px-6 lg:px-8 py-4 sm:py-8">
        {loading ? (
          <LoadingSkeleton type="footballers" />
        ) : (
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
