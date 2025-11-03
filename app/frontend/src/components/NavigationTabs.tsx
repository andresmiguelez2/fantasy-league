import { useNavigate, useLocation } from "react-router-dom";
import { Button } from "@/components/ui/button";

interface NavigationTabsProps {
  leagueId?: string;
}

export const NavigationTabs = ({ leagueId }: NavigationTabsProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  
  const tabs = [
    { id: "league", label: "L", path: leagueId ? `/league/${leagueId}` : "/league/1" },
    { id: "squad", label: "S", path: "/squad" },
    { id: "market", label: "M", path: "/market" },
  ];
  
  const isActive = (path: string) => location.pathname === path;
  
  return (
    <div className="border-b border-border bg-card">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex gap-2 py-3">
          {tabs.map((tab) => (
            <Button
              key={tab.id}
              variant={isActive(tab.path) ? "default" : "outline"}
              onClick={() => navigate(tab.path)}
              className="rounded-full min-w-[3rem]"
            >
              {tab.label}
            </Button>
          ))}
        </div>
      </div>
    </div>
  );
};
