import { useNavigate, useLocation, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";

interface NavigationTabsProps {
  leagueId?: string;
}

export const NavigationTabs = ({ leagueId: leagueIdProp }: NavigationTabsProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { leagueId: leagueIdParam } = useParams<{ leagueId: string }>();
  
  // Use the prop if provided, otherwise fall back to URL param
  const leagueId = leagueIdProp ?? leagueIdParam;
  const leagueBase = leagueId ? `/league/${leagueId}` : "";
  
  const mainTabs = [
    { id: "league", label: "Leaderboard", path: leagueId ? `/league/${leagueId}` : "/league/1" },
    { id: "team", label: "Team", path: `${leagueBase}/squad` },
    { id: "market", label: "Market", path: `${leagueBase}/market` },
    { id: "footballer-info", label: "Footballer Info", path: `${leagueBase}/footballer-info` },
  ];

  const teamSubTabs = [
    { id: "squad", label: "Squad", path: `${leagueBase}/squad` },
    { id: "lineup", label: "Lineup", path: `${leagueBase}/lineup` },
    { id: "fixtures", label: "Fixtures", path: `${leagueBase}/fixtures` },
  ];

  const marketSubTabs = [
    { id: "current-market", label: "Current Market", path: `${leagueBase}/market` },
    { id: "incoming-bids", label: "Incoming Bids", path: `${leagueBase}/market/incoming` },
    { id: "outgoing-bids", label: "Outgoing Bids", path: `${leagueBase}/market/outgoing` },
  ];
  
  const isMainTabActive = (tab: typeof mainTabs[0]) => {
    if (tab.id === "team") {
      const squadPath = `${leagueBase}/squad`;
      const lineupPath = `${leagueBase}/lineup`;
      const fixturesPath = `${leagueBase}/fixtures`;
      return (
        location.pathname === squadPath ||
        location.pathname.startsWith(squadPath + "/") ||
        location.pathname === lineupPath ||
        location.pathname === fixturesPath ||
        // Legacy paths
        location.pathname === "/squad" ||
        location.pathname.startsWith("/squad/") ||
        location.pathname === "/lineup" ||
        location.pathname === "/fixtures"
      );
    }
    if (tab.id === "market") {
      return location.pathname.startsWith(`${leagueBase}/market`) || location.pathname.startsWith("/market");
    }
    if (tab.id === "footballer-info") {
      return (
        location.pathname === `${leagueBase}/footballer-info` ||
        location.pathname === "/footballer-info"
      );
    }
    return location.pathname === tab.path;
  };

  const isSubTabActive = (path: string) => {
    const marketPath = `${leagueBase}/market`;
    if (path === marketPath || path === "/market") {
      return location.pathname === marketPath || location.pathname === "/market";
    }
    return location.pathname === path || location.pathname.startsWith(path + "/");
  };

  const squadPath = `${leagueBase}/squad`;
  const showTeamSubTabs =
    location.pathname === squadPath ||
    location.pathname.startsWith(squadPath + "/") ||
    location.pathname === `${leagueBase}/lineup` ||
    location.pathname === `${leagueBase}/fixtures` ||
    // Legacy paths
    location.pathname === "/squad" ||
    location.pathname.startsWith("/squad/") ||
    location.pathname === "/lineup" ||
    location.pathname === "/fixtures";

  const showMarketSubTabs =
    location.pathname.startsWith(`${leagueBase}/market`) ||
    location.pathname.startsWith("/market");
  
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
