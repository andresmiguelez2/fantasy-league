import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { joinLeague, fetchPlayerNames, setActiveLeagueContext } from "@/lib/api";
import { useNavigate } from "react-router-dom";

interface JoinLeagueDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onJoined: () => void;
  initialInviteCode?: string;
  leagueName?: string;
}

export const JoinLeagueDialog = ({
  open,
  onOpenChange,
  onJoined,
  initialInviteCode = "",
  leagueName,
}: JoinLeagueDialogProps) => {
  const [inviteCode, setInviteCode] = useState(initialInviteCode);
  const [playerName, setPlayerName] = useState("");
  const [previousNames, setPreviousNames] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    if (open) {
      setInviteCode(initialInviteCode);
      setPlayerName("");
      setError(null);
      fetchPlayerNames().then(setPreviousNames).catch(() => setPreviousNames([]));
    }
  }, [open, initialInviteCode]);

  const handleSubmit = async () => {
    if (!inviteCode.trim() || !playerName.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await joinLeague(inviteCode.trim(), playerName.trim());
      if (result.status === "success" && result.league) {
        await setActiveLeagueContext(String(result.league.id)).catch(() => {});
        onJoined();
        onOpenChange(false);
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

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Join League</DialogTitle>
          <DialogDescription>
            {leagueName
              ? `Enter your player name to join "${leagueName}".`
              : "Enter an invite code and your player name to join a league."}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {!leagueName && (
            <div className="space-y-2">
              <Label htmlFor="join-invite-code">Invite Code</Label>
              <Input
                id="join-invite-code"
                value={inviteCode}
                onChange={(e) => setInviteCode(e.target.value)}
                placeholder="Paste invite code here"
              />
            </div>
          )}

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
                <span className="text-xs text-muted-foreground">Previous names:</span>
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
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)} disabled={loading}>
            Cancel
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={loading || !inviteCode.trim() || !playerName.trim()}
          >
            {loading ? "Joining…" : "Join League"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
