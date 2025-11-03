import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { LeagueCard } from "@/components/LeagueCard";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { fetchLeagues, League } from "@/lib/api";

const Landing = () => {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadLeagues = async () => {
      setLoading(true);
      const data = await fetchLeagues();
      setLeagues(data);
      setLoading(false);
    };
    
    loadLeagues();
  }, []);
  
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <h2 className="text-xl font-semibold mb-6">Leagues</h2>
        
        {loading ? (
          <LoadingSkeleton type="leagues" />
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
