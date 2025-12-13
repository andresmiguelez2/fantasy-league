import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

interface BidReplyDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  footballerName: string;
  bidAmount: number;
}

export const BidReplyDialog = ({
  open,
  onOpenChange,
  footballerName,
  bidAmount,
}: BidReplyDialogProps) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Reply to Bid</DialogTitle>
        </DialogHeader>
        
        <div className="py-4">
          <p className="text-muted-foreground mb-2">
            Bid for <span className="font-semibold text-foreground">{footballerName}</span>
          </p>
          <p className="text-2xl font-bold text-primary">
            {formatCurrency(bidAmount)}
          </p>
        </div>

        <DialogFooter className="flex gap-2 sm:gap-0">
          <Button
            variant="destructive"
            onClick={() => onOpenChange(false)}
            className="flex-1 sm:flex-none"
          >
            Decline
          </Button>
          <Button
            variant="default"
            onClick={() => onOpenChange(false)}
            className="flex-1 sm:flex-none"
          >
            Accept
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
