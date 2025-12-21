import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";

interface NavigationTabsProps {
  leagueId?: string;
}

export const NavigationTabs = ({ leagueId }: NavigationTabsProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const mainTabs = [
    { id: "league", label: "Leaderboard", path: leagueId ? `/league/${leagueId}` : "/league/1" },
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
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        {/* Main Tabs */}
        <div className="flex gap-2 py-3">
          {mainTabs.map((tab) => (
            <Button
              key={tab.id}
              variant={isMainTabActive(tab) ? "default" : "outline"}
              onClick={() => navigate(tab.path)}
              className="rounded-full min-w-[3rem]"
            >
              {tab.label}
            </Button>
          ))}
        </div>

        {/* Team SubTabs */}
        {showTeamSubTabs && (
          <div className="flex gap-2 pb-3">
            {teamSubTabs.map((tab) => (
              <Button
                key={tab.id}
                variant={isSubTabActive(tab.path) ? "secondary" : "ghost"}
                onClick={() => navigate(tab.path)}
                className="rounded-full min-w-[3rem] text-sm"
                size="sm"
              >
                {tab.label}
              </Button>
            ))}
          </div>
        )}

        {/* Market SubTabs */}
        {showMarketSubTabs && (
          <div className="flex gap-2 pb-3">
            {marketSubTabs.map((tab) => (
              <Button
                key={tab.id}
                variant={isSubTabActive(tab.path) ? "secondary" : "ghost"}
                onClick={() => navigate(tab.path)}
                className="rounded-full min-w-[3rem] text-sm"
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
