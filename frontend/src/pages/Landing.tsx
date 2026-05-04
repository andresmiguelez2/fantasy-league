import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { LeagueCard } from "@/components/LeagueCard";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { CreateLeagueDialog } from "@/components/CreateLeagueDialog";
import { JoinLeagueDialog } from "@/components/JoinLeagueDialog";
import { fetchLeagues, League } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Plus, UserPlus } from "lucide-react";

const PENDING_INVITE_KEY = "pendingInviteCode";

const Landing = () => {
  const [leagues, setLeagues] = useState<League[]>([]);
  const [loading, setLoading] = useState(true);
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [joinDialogOpen, setJoinDialogOpen] = useState(false);
  const [pendingInviteCode, setPendingInviteCode] = useState("");

  const loadLeagues = async () => {
    setLoading(true);
    const data = await fetchLeagues();
    setLeagues(data);
    setLoading(false);
  };

  useEffect(() => {
    loadLeagues();

    // Open the join dialog automatically if the user was redirected here after login
    const stored = localStorage.getItem(PENDING_INVITE_KEY);
    if (stored) {
      localStorage.removeItem(PENDING_INVITE_KEY);
      setPendingInviteCode(stored);
      setJoinDialogOpen(true);
    }
  }, []);
  
  return (
    <div className="min-h-screen bg-background">
      <Header />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold">Leagues</h2>
          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={() => { setPendingInviteCode(""); setJoinDialogOpen(true); }} size="sm">
              <UserPlus className="w-4 h-4 mr-2" />
              Join League
            </Button>
            <Button onClick={() => setCreateDialogOpen(true)} size="sm">
              <Plus className="w-4 h-4 mr-2" />
              New League
            </Button>
          </div>
        </div>
        
        {loading ? (
          <LoadingSkeleton type="leagues" />
        ) : (
          <div className="space-y-4 max-w-2xl">
            {leagues.map((league) => (
              <LeagueCard key={league.id} id={league.id} name={league.name} />
            ))}
          </div>
        )}

        <CreateLeagueDialog
          open={createDialogOpen}
          onOpenChange={setCreateDialogOpen}
          onCreated={loadLeagues}
        />

        <JoinLeagueDialog
          open={joinDialogOpen}
          onOpenChange={setJoinDialogOpen}
          onJoined={loadLeagues}
          initialInviteCode={pendingInviteCode}
        />
      </main>
    </div>
  );
};

export default Landing;
