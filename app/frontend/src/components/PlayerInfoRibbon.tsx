import { useEffect, useState } from "react";
import { fetchPlayerInfo, PlayerInfo } from "@/lib/api";
import { User, Wallet } from "lucide-react";
import { useAuth } from "@/contexts/AuthContext";

export const PlayerInfoRibbon = () => {
  const [playerInfo, setPlayerInfo] = useState<PlayerInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const { user } = useAuth();
  const playerId = user?.playerId?.toString();

  useEffect(() => {
    if (!playerId) {
      setLoading(false);
      return;
    }
    const loadPlayerInfo = async () => {
      try {
        const data = await fetchPlayerInfo(playerId);
        setPlayerInfo(data);
      } catch (error) {
        console.error('Failed to fetch player info:', error);
        setPlayerInfo(null);
      } finally {
        setLoading(false);
      }
    };

    loadPlayerInfo();
  }, [playerId]);

  if (loading || !playerInfo) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-card/95 backdrop-blur supports-[backdrop-filter]:bg-card/80">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-3">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <User className="h-4 w-4 text-muted-foreground" />
            <span className="font-semibold text-foreground">{playerInfo.name}</span>
          </div>
          <div className="flex items-center gap-2">
            <Wallet className="h-4 w-4 text-muted-foreground" />
            <span className="font-semibold text-foreground">
              €{playerInfo.budget.toLocaleString()}
            </span>
          </div>
        </div>
      </div>
    </div>
  );
};
