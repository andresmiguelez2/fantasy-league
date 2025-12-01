import { useState, useEffect } from "react";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { fetchLineupFormation } from "@/lib/api";
import { Card, CardContent } from "@/components/ui/card";
import { Loader2 } from "lucide-react";

const Lineup = () => {
  const [formation, setFormation] = useState<number[]>([]);
  const [loading, setLoading] = useState(true);
  const playerId = localStorage.getItem("playerId") || "1";

  useEffect(() => {
    const loadFormation = async () => {
      try {
        const data = await fetchLineupFormation(playerId);
        setFormation(data);
      } catch (error) {
        console.error("Error fetching lineup:", error);
        // Default formation if API fails
        setFormation([4, 4, 2]);
      } finally {
        setLoading(false);
      }
    };

    loadFormation();
  }, [playerId]);

  const getFormationString = () => {
    return formation.join('-');
  };

  const renderRow = (count: number, rowIndex: number) => {
    return (
      <div className="flex justify-center gap-6 w-full" style={{ marginBottom: rowIndex === 0 ? '3rem' : '2rem' }}>
        {Array.from({ length: count }).map((_, index) => (
          <div
            key={`${rowIndex}-${index}`}
            className="w-24 h-28 bg-card border-2 border-primary rounded-lg flex items-center justify-center hover:bg-primary/10 transition-colors cursor-pointer shadow-lg"
          >
            <span className="text-sm text-muted-foreground font-medium">Empty</span>
          </div>
        ))}
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <NavigationTabs />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between mb-6">
            <h1 className="text-3xl font-bold">Lineup</h1>
            {!loading && formation.length > 0 && (
              <div className="bg-primary text-primary-foreground px-4 py-2 rounded-full font-bold text-lg shadow-md">
                {getFormationString()}
              </div>
            )}
          </div>
          
          {loading ? (
            <div className="flex justify-center items-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : (
            <Card className="overflow-hidden">
              <CardContent className="p-0">
                <div 
                  className="relative w-full bg-gradient-to-b from-green-600 to-green-700 p-8"
                  style={{ aspectRatio: '3/4' }}
                >
                  {/* Pitch markings */}
                  <div className="absolute inset-4 border-2 border-white/40 rounded-lg">
                    {/* Center circle */}
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-24 h-24 border-2 border-white/40 rounded-full" />
                    <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-2 h-2 bg-white/40 rounded-full" />
                    
                    {/* Center line */}
                    <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-white/40" />
                    
                    {/* Goal areas */}
                    <div className="absolute top-0 left-1/2 -translate-x-1/2 w-32 h-12 border-2 border-white/40 border-t-0" />
                    <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-32 h-12 border-2 border-white/40 border-b-0" />
                  </div>

                  {/* Player positions */}
                  <div className="relative h-full flex flex-col justify-between py-8">
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
    </div>
  );
};

export default Lineup;

