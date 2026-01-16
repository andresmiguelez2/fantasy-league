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
    if (showBackButton) {
      navigate("/");
    }
  };

  const handleLogout = () => {
    logout();
    toast({
      title: 'Logged out',
      description: 'You have been logged out successfully',
    });
    navigate("/login");
  };

  return (
    <header className="border-b border-border bg-card">
      <div className="container mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          <Button
            variant="ghost"
            onClick={handleFantasyClick}
            className={`text-lg font-semibold ${
              showBackButton ? "cursor-pointer hover:bg-accent" : "cursor-default hover:bg-transparent"
            }`}
          >
            Fantasy
          </Button>
          
          <div className="flex items-center gap-4">
            {isAuthenticated && user && (
              <span className="text-sm text-muted-foreground">
                Welcome, {user.username}
              </span>
            )}
            {isAuthenticated ? (
              <Button
                variant="outline"
                onClick={handleLogout}
                className="rounded-full"
              >
                Log out
              </Button>
            ) : (
              <Button
                variant="outline"
                onClick={() => navigate("/login")}
                className="rounded-full"
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
