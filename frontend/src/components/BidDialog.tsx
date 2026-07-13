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
  onSubmit: (amount: number) => void;
}

export const BidDialog = ({
  open,
  onOpenChange,
  footballerName,
  footballerValue,
  currentBid,
  onSubmit,
}: BidDialogProps) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const [bidAmount, setBidAmount] = useState(currentBid ? currentBid.toString() : "");

  useEffect(() => {
    setBidAmount(currentBid ? currentBid.toString() : "");
  }, [currentBid, open, footballerValue]);
  
  const handleSubmit = () => {
    onSubmit(Number(bidAmount));
    onOpenChange(false);
  };
  
  const handleDeleteBid = () => {
    onSubmit(0);
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
