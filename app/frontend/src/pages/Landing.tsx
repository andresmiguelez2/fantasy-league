import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { LeagueCard } from "@/components/LeagueCard";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { CreateLeagueDialog } from "@/components/CreateLeagueDialog";
import { fetchLeagues, League } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Plus } from "lucide-react";

const Landing = () => {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);

  const loadLeagues = async () => {
    setLoading(true);
    const data = await fetchLeagues();
    setLeagues(data);
    setLoading(false);
  };

  useEffect(() => {
    loadLeagues();
  }, []);
  
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Leagues</h2>
          <Button onClick={() => setCreateDialogOpen(true)} size="sm">
            <Plus className="w-4 h-4 mr-2" />
            New League
          </Button>
        </div>
        
        {loading ? (
          <LoadingSkeleton type="leagues" />
        ) : (
          <div className="space-y-4 max-w-2xl">
            {leagues.map((league) => (
              <LeagueCard key={league.id} id={league.id} name={league.name} />
            ))}
          </div>
        )}

        <CreateLeagueDialog
          open={createDialogOpen}
          onOpenChange={setCreateDialogOpen}
          onCreated={loadLeagues}
        />
      </main>
    </div>
  );
};

export default Landing;
