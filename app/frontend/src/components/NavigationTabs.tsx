import { useNavigate, useLocation, useParams } from "react-router-dom";
import { Button } from "@/components/ui/button";

interface NavigationTabsProps {
  leagueId?: string;
}

export const NavigationTabs = ({ leagueId: leagueIdProp }: NavigationTabsProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { leagueId: leagueIdParam } = useParams<{ leagueId: string }>();

  // Use prop if provided (for backward compatibility), otherwise fall back to URL param
  const leagueId = leagueIdProp || leagueIdParam;
  
  const mainTabs = [
    { id: "league", label: "Leaderboard", path: `/league/${leagueId}` },
    { id: "team", label: "Team", path: `/league/${leagueId}/squad` },
    { id: "market", label: "Market", path: `/league/${leagueId}/market` },
    { id: "footballer-info", label: "Footballer Info", path: leagueId ? `/league/${leagueId}/footballer-info` : "/footballer-info" },
  ];

  const teamSubTabs = [
    { id: "squad", label: "Squad", path: `/league/${leagueId}/squad` },
    { id: "lineup", label: "Lineup", path: `/league/${leagueId}/lineup` },
    { id: "fixtures", label: "Fixtures", path: `/league/${leagueId}/fixtures` },
  ];

  const marketSubTabs = [
    { id: "current-market", label: "Current Market", path: `/league/${leagueId}/market` },
    { id: "incoming-bids", label: "Incoming Bids", path: `/league/${leagueId}/market/incoming` },
    { id: "outgoing-bids", label: "Outgoing Bids", path: `/league/${leagueId}/market/outgoing` },
  ];
  
  const isMainTabActive = (tab: typeof mainTabs[0]) => {
    if (tab.id === "team") {
      return (
        location.pathname === `/league/${leagueId}/squad` ||
        location.pathname.startsWith(`/league/${leagueId}/squad/`) ||
        location.pathname === `/league/${leagueId}/lineup` ||
        location.pathname === `/league/${leagueId}/fixtures`
      );
    }
    if (tab.id === "market") {
      return location.pathname.startsWith(`/league/${leagueId}/market`);
    }
    if (tab.id === "footballer-info") {
      return (
        location.pathname === "/footballer-info" ||
        location.pathname === `/league/${leagueId}/footballer-info`
      );
    }
    return location.pathname === tab.path;
  };

  const isSubTabActive = (path: string) => {
    if (path === `/league/${leagueId}/market`) {
      return location.pathname === `/league/${leagueId}/market`;
    }
    return location.pathname === path || location.pathname.startsWith(path + "/");
  };

  const showTeamSubTabs =
    location.pathname === `/league/${leagueId}/squad` ||
    location.pathname.startsWith(`/league/${leagueId}/squad/`) ||
    location.pathname === `/league/${leagueId}/lineup` ||
    location.pathname === `/league/${leagueId}/fixtures`;
  const showMarketSubTabs = location.pathname.startsWith(`/league/${leagueId}/market`);
  
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
