import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { LeagueCard } from "@/components/LeagueCard";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { fetchLeagues, League } from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";

const Landing = () => {
  const { token } = useAuth();
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadLeagues = async () => {
      setLoading(true);
      const data = await fetchLeagues(token ?? undefined);
      setLeagues(data);
      setLoading(false);
    };
    
    loadLeagues();
  }, [token]);
  
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-xl font-semibold mb-6">Leagues</h2>
        
        {loading ? (
          <LoadingSkeleton type="leagues" />
        ) : leagues.length === 0 ? (
          <p className="text-muted-foreground">You are not a member of any league yet.</p>
        ) : (
          <div className="space-y-4 max-w-2xl">
            {leagues.map((league) => (
              <LeagueCard key={league.id} id={league.id} name={league.name} />
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default Landing;
