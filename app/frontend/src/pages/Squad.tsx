import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { SquadRow } from "@/components/SquadRow";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { fetchSquadFootballers, Footballer } from "@/lib/api";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";

const Squad = () => {
  const [footballers, setFootballers] = useState<Footballer[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadFootballers = async () => {
      setLoading(true);
      // TODO: Replace 'player_id' with actual player ID from auth or context
      const playerId = '1';
      const data = await fetchSquadFootballers(playerId);
      setFootballers(data);
      setLoading(false);
    };
    
    loadFootballers();
  }, []);
  
  return (
    <div className="min-h-screen bg-background">
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
                  <TableHead className="text-center">Value</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {footballers.map((footballer) => (
                  <SquadRow
                    key={footballer.id}
                    name={footballer.name}
                    value={footballer.value}
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

export default Squad;
