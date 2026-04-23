import { useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Header } from "@/components/Header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  fetchLeagueByInviteCode,
  joinLeague,
  fetchPlayerNames,
  setActiveLeagueContext,
} from "@/lib/api";
import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";

const PENDING_INVITE_KEY = "pendingInviteCode";

const JoinLeague = () => {
  const { inviteCode } = useParams<{ inviteCode: string }>();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [leagueName, setLeagueName] = useState<string | null>(null);
  const [fetchError, setFetchError] = useState<string | null>(null);
  const [playerName, setPlayerName] = useState("");
  const [previousNames, setPreviousNames] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [fetchingLeague, setFetchingLeague] = useState(true);

  // Fetch league info from the invite code
  useEffect(() => {
    if (!inviteCode) return;

    setFetchingLeague(true);
    fetchLeagueByInviteCode(inviteCode)
      .then((data) => {
        if (data.status === "success" && data.league) {
          setLeagueName(data.league.name);
        } else {
          setFetchError(data.detail || "Invalid invite code");
        }
      })
      .catch(() => setFetchError("Could not load league information"))
      .finally(() => setFetchingLeague(false));
  }, [inviteCode]);

  // Load previous player names when authenticated
  useEffect(() => {
    if (isAuthenticated) {
      fetchPlayerNames().then(setPreviousNames).catch(() => setPreviousNames([]));
    }
  }, [isAuthenticated]);

  const handleJoin = async () => {
    if (!inviteCode || !playerName.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await joinLeague(inviteCode, playerName.trim());
      if (result.status === "success" && result.league) {
        await setActiveLeagueContext(String(result.league.id)).catch(() => {});
        toast({
          title: result.already_member ? "Already a member" : "Joined!",
          description: result.already_member
            ? `You are already in ${result.league.name}. Redirecting…`
            : `Welcome to ${result.league.name}!`,
        });
        navigate(`/league/${result.league.id}`);
      } else {
        setError(result.detail || "Failed to join league. Please try again.");
      }
    } catch {
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  const handleLoginRedirect = () => {
    if (inviteCode) {
      localStorage.setItem(PENDING_INVITE_KEY, inviteCode);
    }
    navigate("/login");
  };

  if (authLoading || fetchingLeague) {
    return (
      <div className="min-h-screen bg-background">
        <Header />
        <main className="container mx-auto px-4 py-16 flex justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary" />
        </main>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="container mx-auto px-4 py-16 flex justify-center">
        <Card className="w-full max-w-md">
          <CardHeader>
            <CardTitle>Join League</CardTitle>
            {leagueName && !fetchError && (
              <CardDescription>
                You've been invited to join <strong>{leagueName}</strong>.
              </CardDescription>
            )}
          </CardHeader>
          <CardContent>
            {fetchError ? (
              <div className="space-y-4 text-center">
                <p className="text-destructive">{fetchError}</p>
                <Button variant="outline" onClick={() => navigate("/")}>
                  Back to Home
                </Button>
              </div>
            ) : !isAuthenticated ? (
              <div className="space-y-4 text-center">
                <p className="text-muted-foreground">
                  You need to log in or create an account to join this league.
                </p>
                <div className="flex flex-col sm:flex-row gap-2 justify-center">
                  <Button onClick={handleLoginRedirect}>Log In / Register</Button>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <div className="space-y-2">
                  <Label htmlFor="join-player-name">Your Player Name</Label>
                  <Input
                    id="join-player-name"
                    value={playerName}
                    onChange={(e) => setPlayerName(e.target.value)}
                    placeholder="e.g. John's Team"
                  />
                  {previousNames.length > 0 && (
                    <div className="flex flex-wrap items-center gap-2 mt-1">
                      <span className="text-xs text-muted-foreground">
                        Previous names:
                      </span>
                      {previousNames.map((name) => (
                        <button
                          key={name}
                          type="button"
                          onClick={() => setPlayerName(name)}
                          className="text-xs px-2 py-1 rounded-full bg-secondary hover:bg-secondary/80 transition-colors"
                        >
                          {name}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
                {error && <p className="text-sm text-destructive">{error}</p>}
                <div className="flex flex-col sm:flex-row gap-2">
                  <Button
                    variant="outline"
                    onClick={() => navigate("/")}
                    disabled={loading}
                  >
                    Cancel
                  </Button>
                  <Button
                    onClick={handleJoin}
                    disabled={loading || !playerName.trim()}
                    className="flex-1"
                  >
                    {loading ? "Joining…" : "Join League"}
                  </Button>
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      </main>
    </div>
  );
};

export default JoinLeague;
