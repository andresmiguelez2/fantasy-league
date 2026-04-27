import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchLeagueInvite } from "@/lib/api";
import { Copy, Check } from "lucide-react";
import { QRCodeSVG } from "qrcode.react";

interface LeagueInviteDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  leagueId: string;
  leagueName?: string;
}

export const LeagueInviteDialog = ({
  open,
  onOpenChange,
  leagueId,
  leagueName,
}: LeagueInviteDialogProps) => {
  const [inviteLink, setInviteLink] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (!open) return;

    setLoading(true);
    setError(null);
    setCopied(false);

    fetchLeagueInvite(leagueId)
      .then((data) => {
        if (data.status === "success" && data.invite_code) {
          const origin = window.location.origin;
          setInviteLink(`${origin}/join/${data.invite_code}`);
        } else {
          setError(data.detail || "Could not load invite link.");
        }
      })
      .catch(() => setError("Could not load invite link."))
      .finally(() => setLoading(false));
  }, [open, leagueId]);

  const handleCopy = () => {
    navigator.clipboard.writeText(inviteLink).then(() => {
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    });
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Invite Players</DialogTitle>
          <DialogDescription>
            Share this link with anyone you want to invite
            {leagueName ? ` to "${leagueName}"` : ""}.
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {loading && (
            <p className="text-sm text-muted-foreground">Loading invite link…</p>
          )}
          {error && <p className="text-sm text-destructive">{error}</p>}
          {!loading && !error && inviteLink && (
            <div className="space-y-4">
              <div className="space-y-2">
                <Label>Invite Link</Label>
                <div className="flex gap-2">
                  <Input value={inviteLink} readOnly className="flex-1 text-sm" />
                  <Button
                    type="button"
                    variant="outline"
                    size="icon"
                    onClick={handleCopy}
                    title="Copy to clipboard"
                  >
                    {copied ? (
                      <Check className="w-4 h-4 text-green-500" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </Button>
                </div>
                {copied && (
                  <p className="text-xs text-green-600">Copied to clipboard!</p>
                )}
              </div>
              <div className="space-y-2">
                <Label>QR Code</Label>
                <div className="flex justify-center p-4 bg-white rounded-lg border">
                  <QRCodeSVG value={inviteLink} size={180} />
                </div>
                <p className="text-xs text-muted-foreground text-center">
                  Scan to join the league
                </p>
              </div>
            </div>
          )}
        </div>

        <div className="flex justify-end">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
