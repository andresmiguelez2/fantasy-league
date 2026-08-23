import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";

interface HeaderProps {
  showBackButton?: boolean;
}

export const Header = ({ showBackButton = false }: HeaderProps) => {
  const navigate = useNavigate();
  const { isAuthenticated, logout, user } = useAuth();
  const { toast } = useToast();

  const handleFantasyClick = () => {
    navigate("/");
  };

  const handleLogout = () => {
    logout();
    toast({
      title: "Logged out",
      description: "You have been logged out successfully",
    });
    navigate("/login");
  };

  return (
    <header className="border-b border-border bg-card">
      <div className="container mx-auto px-3 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14 sm:h-16">
          <Button
            variant="ghost"
            onClick={handleFantasyClick}
            className="text-base sm:text-lg font-semibold px-2 sm:px-4 cursor-pointer hover:bg-accent"
          >
            Fantasy
          </Button>

          <div className="flex items-center gap-2 sm:gap-4">
            {isAuthenticated && user && (
              <span className="text-xs sm:text-sm text-muted-foreground hidden sm:inline">
                Welcome, {user.username}
              </span>
            )}
            {isAuthenticated ? (
              <Button
                variant="outline"
                onClick={handleLogout}
                className="rounded-full text-xs sm:text-sm px-3 sm:px-4 h-8 sm:h-10"
              >
                Log out
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={() => navigate("/login")}
                className="rounded-full text-xs sm:text-sm px-3 sm:px-4 h-8 sm:h-10"
              >
                Log in
              </Button>
            )}
          </div>
        </div>
      </div>
    </header>
  );
};
