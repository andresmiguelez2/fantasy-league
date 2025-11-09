import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { PlayerRow } from "@/components/PlayerRow";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { PlayerInfoRibbon } from "@/components/PlayerInfoRibbon";
import { fetchLeaderboard, Player } from "@/lib/api";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";

// Sample placeholder data for visualization
const samplePlayers: Player[] = [
  { id: 1, name: "Alice", points: 1245, budget: 85000000, team_value: 315000000 },
  { id: 2, name: "Bob", points: 1189, budget: 42000000, team_value: 358000000 },
  { id: 3, name: "Charlotte", points: 1156, budget: 15000000, team_value: 385000000 },
  { id: 4, name: "Daniel", points: 1098, budget: 92000000, team_value: 308000000 },
  { id: 5, name: "Emma", points: 1067, budget: 38000000, team_value: 362000000 },
  { id: 6, name: "Frank", points: 1023, budget: 105000000, team_value: 295000000 },
  { id: 7, name: "Grace", points: 987, budget: 55000000, team_value: 345000000 },
  { id: 8, name: "Henry", points: 945, budget: 72000000, team_value: 328000000 },
  { id: 9, name: "Ivy", points: 912, budget: 18000000, team_value: 382000000 },
  { id: 10, name: "Jack", points: 876, budget: 125000000, team_value: 275000000 },
];

const League = () => {
  const { leagueId } = useParams();
  const [players, setPlayers] = useState<Player[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadPlayers = async () => {
      setLoading(true);
      try {
        const data = await fetchLeaderboard();
        setPlayers(data);
      } catch (error) {
        console.log('Failed to fetch leaderboard data, using sample data for visualization');
        // Use sample data when API is not available
        setPlayers(samplePlayers);
      } finally {
        setLoading(false);
      }
    };
    
    loadPlayers();
  }, []);
  
  return (
    <div className="min-h-screen bg-background pb-20">
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
                  <TableHead className="text-center">Team Value</TableHead>
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
                  />
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </main>
      <PlayerInfoRibbon />
    </div>
  );
};

export default League;
