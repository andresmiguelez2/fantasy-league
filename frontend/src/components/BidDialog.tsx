import { useEffect, useState } from "react";
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

interface BidDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  footballerName: string;
  footballerValue?: number;
  currentBid?: number;
  currentBidTimestamp?: string;
  onSubmit: (amount: number, timestamp?: string | null) => void | Promise<void>;
}

export const BidDialog = ({
  open,
  onOpenChange,
  footballerName,
  footballerValue,
  currentBid,
  currentBidTimestamp,
  onSubmit,
}: BidDialogProps) => {
  const toLocalDateTimeValue = (timestamp: string) => {
    const date = new Date(timestamp);
    const offset = date.getTimezoneOffset();
    const localDate = new Date(date.getTime() - offset * 60_000);
    return localDate.toISOString().slice(0, 16);
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const [bidAmount, setBidAmount] = useState(currentBid ? currentBid.toString() : "");
  const [scheduledTimestamp, setScheduledTimestamp] = useState("");

  useEffect(() => {
    setBidAmount(currentBid ? currentBid.toString() : "");
    if (currentBidTimestamp && new Date(currentBidTimestamp).getTime() > Date.now()) {
      setScheduledTimestamp(toLocalDateTimeValue(currentBidTimestamp));
      return;
    }
    setScheduledTimestamp("");
  }, [currentBid, currentBidTimestamp, open, footballerValue]);
  
  const handleSubmit = async () => {
    const bidTimestamp = scheduledTimestamp ? new Date(scheduledTimestamp).toISOString() : undefined;
    await onSubmit(Number(bidAmount), bidTimestamp);
    onOpenChange(false);
  };
  
  const handleDeleteBid = async () => {
    await onSubmit(0);
    onOpenChange(false);
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Place Bid</DialogTitle>
          <DialogDescription>
            Place your bid for {footballerName}
          </DialogDescription>
        </DialogHeader>
        
        <div className="space-y-4 py-4">
          {footballerValue !== undefined && (
            <div className="text-sm text-muted-foreground">
              Footballer value: <span className="font-medium text-foreground">{formatCurrency(footballerValue)}</span>
            </div>
          )}

          {currentBid && (
            <div className="text-sm text-muted-foreground">
              Current bid: {formatCurrency(currentBid)}
            </div>
          )}
          
          <div className="space-y-2">
            <Label htmlFor="amount">Your bid amount (€)</Label>
            <Input
              id="amount"
              type="number"
              value={bidAmount}
              onChange={(e) => setBidAmount(e.target.value)}
              placeholder={currentBid === undefined && footballerValue !== undefined ? formatCurrency(footballerValue) : undefined}
              min={currentBid ? currentBid + 1 : 1}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="scheduled-timestamp">Schedule for later (optional)</Label>
            <Input
              id="scheduled-timestamp"
              type="datetime-local"
              value={scheduledTimestamp}
              onChange={(e) => setScheduledTimestamp(e.target.value)}
            />
          </div>
        </div>
        
        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          {currentBid && (
            <Button variant="destructive" onClick={handleDeleteBid}>
              Delete Bid
            </Button>
          )}
          <Button onClick={handleSubmit}>
            Place Bid
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
