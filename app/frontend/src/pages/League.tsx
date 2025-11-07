import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { PlayerRow } from "@/components/PlayerRow";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { fetchLeaderboard, Player } from "@/lib/api";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const League = () => {
  const { leagueId } = useParams();
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadPlayers = async () => {
      setLoading(true);
      const data = await fetchLeaderboard();
      setPlayers(data);
      setLoading(false);
    };
    
    loadPlayers();
  }, []);
  
  return (
    <div className="min-h-screen bg-background">
      <Header showBackButton />
      <NavigationTabs leagueId={leagueId} />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <LoadingSkeleton type="players" />
        ) : (
          <div className="max-w-4xl">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Player</TableHead>
                  <TableHead className="text-center">Points</TableHead>
                  <TableHead className="text-center">Budget</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {players.map((player) => (
                  <PlayerRow
                    key={player.id}
                    playerId={player.id}
                    name={player.name}
                    points={player.points}
                    budget={player.budget}
                  />
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </main>
    </div>
  );
};

export default League;
