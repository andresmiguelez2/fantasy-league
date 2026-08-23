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
  bidderName: string;
  bidAmount: number;
  onAccept: () => void;
  onDecline: () => void;
}

export const BidReplyDialog = ({
  open,
  onOpenChange,
  footballerName,
  bidderName,
  bidAmount,
  onAccept,
  onDecline,
}: BidReplyDialogProps) => {
  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "EUR",
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
            Bid for <span className="font-semibold text-foreground">{footballerName}</span> from{" "}
            <span className="font-semibold text-foreground">{bidderName}</span>
          </p>
          <p className="text-2xl font-bold text-primary">{formatCurrency(bidAmount)}</p>
        </div>

        <DialogFooter className="flex gap-2 sm:gap-0">
          <Button variant="destructive" onClick={onDecline} className="flex-1 sm:flex-none">
            Decline
          </Button>
          <Button
            onClick={onAccept}
            className="flex-1 sm:flex-none bg-green-600 hover:bg-green-700 text-white"
          >
            Accept
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
