import { useEffect } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { getActiveLeagueId, setActiveLeagueContext } from "@/lib/api";

interface NavigationTabsProps {
  leagueId?: string;
}

export const NavigationTabs = ({ leagueId }: NavigationTabsProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const activeLeagueId = leagueId || getActiveLeagueId();

  useEffect(() => {
    if (leagueId && leagueId !== getActiveLeagueId()) {
      setActiveLeagueContext(leagueId).catch((error) => {
        console.error("Failed to update active league context:", error);
      });
    }
  }, [leagueId]);
  
  const mainTabs = [
    { id: "league", label: "Leaderboard", path: `/league/${activeLeagueId}` },
    { id: "team", label: "Team", path: "/squad" },
    { id: "market", label: "Market", path: "/market" },
    { id: "footballer-info", label: "Footballer Info", path: "/footballer-info" },
  ];

  const teamSubTabs = [
    { id: "squad", label: "Squad", path: "/squad" },
    { id: "lineup", label: "Lineup", path: "/lineup" },
    { id: "fixtures", label: "Fixtures", path: "/fixtures" },
  ];

  const marketSubTabs = [
    { id: "current-market", label: "Current Market", path: "/market" },
    { id: "incoming-bids", label: "Incoming Bids", path: "/market/incoming" },
    { id: "outgoing-bids", label: "Outgoing Bids", path: "/market/outgoing" },
    { id: "future-bids", label: "Future Bids", path: "/market/future" },
    { id: "market-history", label: "Market History", path: "/market/history" },
  ];
  
  const isMainTabActive = (tab: typeof mainTabs[0]) => {
    if (tab.id === "team") {
      return location.pathname === "/squad" || location.pathname.startsWith("/squad/") || location.pathname === "/lineup" || location.pathname === "/fixtures";
    }
    if (tab.id === "market") {
      return location.pathname.startsWith("/market");
    }
    return location.pathname === tab.path;
  };

  const isSubTabActive = (path: string) => {
    if (path === "/market") {
      return location.pathname === "/market";
    }
    return location.pathname === path || location.pathname.startsWith(path + "/");
  };

  const showTeamSubTabs = location.pathname === "/squad" || location.pathname.startsWith("/squad/") || location.pathname === "/lineup" || location.pathname === "/fixtures";
  const showMarketSubTabs = location.pathname.startsWith("/market");
  
  return (
    <div className="border-b border-border bg-card">
      <div className="container mx-auto px-3 sm:px-6 lg:px-8">
        {/* Main Tabs */}
        <div className="flex gap-1.5 sm:gap-2 py-2 sm:py-3 overflow-x-auto scrollbar-hide">
          {mainTabs.map((tab) => (
            <Button
              key={tab.id}
              variant={isMainTabActive(tab) ? "default" : "outline"}
              onClick={() => navigate(tab.path)}
              className="rounded-full min-w-fit px-3 sm:px-4 text-xs sm:text-sm h-8 sm:h-10 whitespace-nowrap flex-shrink-0"
            >
              {tab.label}
            </Button>
          ))}
        </div>

        {/* Team SubTabs */}
        {showTeamSubTabs && (
          <div className="flex gap-1.5 sm:gap-2 pb-2 sm:pb-3 overflow-x-auto scrollbar-hide">
            {teamSubTabs.map((tab) => (
              <Button
                key={tab.id}
                variant={isSubTabActive(tab.path) ? "secondary" : "ghost"}
                onClick={() => navigate(tab.path)}
                className="rounded-full min-w-fit px-3 sm:px-4 text-xs sm:text-sm h-7 sm:h-9 whitespace-nowrap flex-shrink-0"
                size="sm"
              >
                {tab.label}
              </Button>
            ))}
          </div>
        )}

        {/* Market SubTabs */}
        {showMarketSubTabs && (
          <div className="flex gap-1.5 sm:gap-2 pb-2 sm:pb-3 overflow-x-auto scrollbar-hide">
            {marketSubTabs.map((tab) => (
              <Button
                key={tab.id}
                variant={isSubTabActive(tab.path) ? "secondary" : "ghost"}
                onClick={() => navigate(tab.path)}
                className="rounded-full min-w-fit px-3 sm:px-4 text-xs sm:text-sm h-7 sm:h-9 whitespace-nowrap flex-shrink-0"
                size="sm"
              >
                {tab.label}
              </Button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
