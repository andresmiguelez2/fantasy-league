import { useEffect, useState } from "react";
import { fetchPlayerInfo, PlayerInfo } from "@/lib/api";
import { Card } from "@/components/ui/card";
import { User, Wallet } from "lucide-react";

export const PlayerInfoRibbon = () => {
  const [playerInfo, setPlayerInfo] = useState<PlayerInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const playerId = '1'; // Hardcoded for now

  useEffect(() => {
    const loadPlayerInfo = async () => {
      try {
        const data = await fetchPlayerInfo(playerId);
        setPlayerInfo(data);
      } catch (error) {
        console.error('Failed to fetch player info:', error);
        // Set placeholder data if fetch fails
        setPlayerInfo({
          id: 1,
          name: 'Player Name',
          points: 0,
          budget: 100000,
        });
      } finally {
        setLoading(false);
      }
    };

    loadPlayerInfo();
  }, []);

  // Show placeholder while loading
  const displayInfo = loading 
    ? { name: 'Loading...', budget: 0 }
    : playerInfo || { name: 'Player Name', budget: 100000 };

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <User className="h-4 w-4 text-muted-foreground" />
            <span className="font-semibold text-foreground">{displayInfo.name}</span>
          </div>
          <div className="flex items-center gap-2">
            <Wallet className="h-4 w-4 text-muted-foreground" />
            <span className="font-semibold text-foreground">
              €{displayInfo.budget.toLocaleString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
