import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { AuthDialog } from "./AuthDialog";

interface HeaderProps {
  showBackButton?: boolean;
}

export const Header = ({ showBackButton = false }: HeaderProps) => {
  const [authOpen, setAuthOpen] = useState(false);
  const navigate = useNavigate();

  const handleFantasyClick = () => {
    if (showBackButton) {
      navigate("/");
    }
  };

  return (
    <>
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
            
            <Button
              variant="outline"
              onClick={() => setAuthOpen(true)}
              className="rounded-full"
            >
              Log in / Log out
            </Button>
          </div>
        </div>
      </header>
      
      <AuthDialog open={authOpen} onOpenChange={setAuthOpen} />
    </>
  );
};
