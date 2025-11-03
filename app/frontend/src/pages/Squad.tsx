import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { FootballerCard } from "@/components/FootballerCard";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { fetchSquadFootballers, Footballer } from "@/lib/api";

const Squad = () => {
  const [footballers, setFootballers] = useState<Footballer[]>([]);
  const [loading, setLoading] = useState(true);
  
  useEffect(() => {
    const loadFootballers = async () => {
      setLoading(true);
      const data = await fetchSquadFootballers();
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
          <div className="space-y-3 max-w-2xl">
            {footballers.map((footballer) => (
              <FootballerCard
                key={footballer.id}
                name={footballer.name}
              />
            ))}
          </div>
        )}
      </main>
    </div>
  );
};

export default Squad;
