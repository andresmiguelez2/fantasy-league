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
import { createLeague, fetchPlayerNames } from "@/lib/api";

interface CreateLeagueDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onCreated: () => void;
}

export const CreateLeagueDialog = ({
  open,
  onOpenChange,
  onCreated,
}: CreateLeagueDialogProps) => {
  const [leagueName, setLeagueName] = useState("");
  const [playerName, setPlayerName] = useState("");
  const [previousNames, setPreviousNames] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      setLeagueName("");
      setPlayerName("");
      setError(null);
      fetchPlayerNames().then(setPreviousNames).catch(() => setPreviousNames([]));
    }
  }, [open]);

  const handleSubmit = async () => {
    if (!leagueName.trim() || !playerName.trim()) return;

    setLoading(true);
    setError(null);

    try {
      const result = await createLeague(leagueName.trim(), playerName.trim());
      if (result.status === "success") {
        onCreated();
        onOpenChange(false);
      } else {
        setError(result.detail || "Failed to create league. Please try again.");
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
          <DialogTitle>Create New League</DialogTitle>
          <DialogDescription>
            Enter a league name and your player name to get started.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          <div className="space-y-2">
            <Label htmlFor="league-name">League Name</Label>
            <Input
              id="league-name"
              value={leagueName}
              onChange={(e) => setLeagueName(e.target.value)}
              placeholder="e.g. Friends League 2026"
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="player-name">Your Player Name</Label>
            <Input
              id="player-name"
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
            disabled={loading || !leagueName.trim() || !playerName.trim()}
          >
            {loading ? "Creating…" : "Create League"}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
