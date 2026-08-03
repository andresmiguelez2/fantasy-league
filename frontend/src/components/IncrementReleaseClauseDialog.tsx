import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { fetchReleaseClauseData } from "@/lib/api";

interface IncrementReleaseClauseDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  footballerName: string;
  footballerId: number;
  onSubmit: (increment: number) => Promise<boolean>;
}

export const IncrementReleaseClauseDialog = ({
  open,
  onOpenChange,
  footballerName,
  footballerId,
  onSubmit,
}: IncrementReleaseClauseDialogProps) => {
  const [incrementInput, setIncrementInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [currentReleaseClause, setCurrentReleaseClause] = useState<number | null>(null);
  const [fetchingClause, setFetchingClause] = useState(false);

  useEffect(() => {
    if (open && footballerId) {
      setFetchingClause(true);
      fetchReleaseClauseData(footballerId)
        .then((data) => {
          setCurrentReleaseClause(data.release_clause ?? null);
        })
        .catch(() => {
          setCurrentReleaseClause(null);
        })
        .finally(() => {
          setFetchingClause(false);
        });
    }
  }, [open, footballerId]);

  const parsedIncrement = Number(incrementInput);
  const isValid = Number.isInteger(parsedIncrement) && parsedIncrement > 0;
  const newReleaseClause =
    isValid && currentReleaseClause !== null
      ? currentReleaseClause + parsedIncrement
      : null;

  const formatValue = (val: number) =>
    new Intl.NumberFormat("en-ES", {
      style: "currency",
      currency: "EUR",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(val);

  const handleSubmit = async () => {
    if (!isValid) return;
    setLoading(true);
    const success = await onSubmit(parsedIncrement);
    setLoading(false);
    if (success) {
      setIncrementInput("");
      onOpenChange(false);
    }
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setIncrementInput("");
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Increment Release Clause</DialogTitle>
          <DialogDescription>
            Increase the release clause for {footballerName}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4 py-4">
          {fetchingClause ? (
            <div className="text-sm text-muted-foreground">
              Loading current release clause...
            </div>
          ) : currentReleaseClause !== null ? (
            <div className="space-y-1">
              <div className="text-sm text-muted-foreground">Current release clause</div>
              <div className="text-lg font-semibold">{formatValue(currentReleaseClause)}</div>
            </div>
          ) : null}

          <div className="space-y-2">
            <Label htmlFor="increment-release-clause">Increment amount (€)</Label>
            <Input
              id="increment-release-clause"
              type="number"
              value={incrementInput}
              onChange={(e) => setIncrementInput(e.target.value)}
              min={1}
              step={1}
              placeholder="Enter amount to add"
            />
          </div>

          {newReleaseClause !== null && (
            <div className="space-y-1">
              <div className="text-sm text-muted-foreground">New release clause</div>
              <div className="text-lg font-semibold text-primary">
                {formatValue(newReleaseClause)}
              </div>
            </div>
          )}
        </div>

        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button variant="outline" onClick={() => handleOpenChange(false)}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={loading || !isValid}>
            Confirm
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
