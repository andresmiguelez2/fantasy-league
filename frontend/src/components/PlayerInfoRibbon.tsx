import { useEffect, useState } from "react";
import {
  fetchPlayerBidSum,
  fetchPlayerInfo,
  getActivePlayerId,
  getActiveLeagueName,
  PlayerInfo,
} from "@/lib/api";
import { User, Wallet } from "lucide-react";

export const PlayerInfoRibbon = () => {
  const [playerInfo, setPlayerInfo] = useState<PlayerInfo | null>(null);
  const [playerBidSum, setPlayerBidSum] = useState<number>(0);
  const [loading, setLoading] = useState(true);
  const [leagueName, setLeagueName] = useState<string | null>(null);
  const playerId = getActivePlayerId();

  useEffect(() => {
    setLeagueName(getActiveLeagueName());
  }, [playerId]);

  useEffect(() => {
    if (!playerId) {
      setLoading(false);
      return;
    }
    const loadPlayerInfo = async () => {
      try {
        const [playerData, bidSum] = await Promise.all([
          fetchPlayerInfo(playerId),
          fetchPlayerBidSum(playerId),
        ]);
        setPlayerInfo(playerData);
        setPlayerBidSum(bidSum);
      } catch (error) {
        console.error("Failed to fetch player info:", error);
        setPlayerInfo(null);
        setPlayerBidSum(0);
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
            {leagueName && (
              <>
                <span className="text-muted-foreground">|</span>
                <span className="text-sm text-muted-foreground">{leagueName}</span>
              </>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Wallet className="h-4 w-4 text-muted-foreground" />
            <div className="flex flex-col items-end leading-tight">
              <span className="font-semibold text-foreground">
                €{playerInfo.budget.toLocaleString()}
              </span>
              {playerBidSum > 0 && (
                <span className="text-sm font-medium text-red-500">
                  € -{playerBidSum.toLocaleString()}
                </span>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
