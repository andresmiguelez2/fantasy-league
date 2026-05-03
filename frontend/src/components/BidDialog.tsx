import { useState } from "react";
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
  currentBid?: number;
  onSubmit: (amount: number) => void;
}

export const BidDialog = ({
  open,
  onOpenChange,
  footballerName,
  currentBid,
  onSubmit,
}: BidDialogProps) => {
  const [bidAmount, setBidAmount] = useState(currentBid ? currentBid + 1000 : 50000);
  
  const handleSubmit = () => {
    onSubmit(bidAmount);
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
          {currentBid && (
            <div className="text-sm text-muted-foreground">
              Current bid: €{currentBid.toLocaleString()}
            </div>
          )}
          
          <div className="space-y-2">
            <Label htmlFor="amount">Your bid amount (€)</Label>
            <Input
              id="amount"
              type="number"
              value={bidAmount}
              onChange={(e) => setBidAmount(Number(e.target.value))}
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
