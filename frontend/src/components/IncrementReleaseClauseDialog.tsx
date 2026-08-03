import { useState } from "react";
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

interface IncrementReleaseClauseDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  footballerName: string;
  onSubmit: (increment: number) => Promise<boolean>;
}

export const IncrementReleaseClauseDialog = ({
  open,
  onOpenChange,
  footballerName,
  onSubmit,
}: IncrementReleaseClauseDialogProps) => {
  const [incrementInput, setIncrementInput] = useState("");
  const [loading, setLoading] = useState(false);

  const parsedIncrement = Number(incrementInput);
  const isValid = Number.isInteger(parsedIncrement) && parsedIncrement > 0;

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
