import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface FootballerCardProps {
  name: string;
  currentBid?: number;
  showBidButton?: boolean;
  onBid?: () => void;
}

export const FootballerCard = ({ name, currentBid, showBidButton = false, onBid }: FootballerCardProps) => {
  const formatBid = (amount: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(amount);
  };
  
  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };
  
  return (
    <Card className="p-4 flex items-center justify-between fade-in hover-lift border-primary/20 bg-gradient-to-r from-card to-card/80">
      <div className="flex items-center gap-3">
        <Avatar className="h-12 w-12 border-2 border-primary/30">
          <AvatarImage src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${name}`} />
          <AvatarFallback className="bg-gradient-primary text-white font-semibold">
            {getInitials(name)}
          </AvatarFallback>
        </Avatar>
        <span className="font-semibold text-foreground">{name}</span>
      </div>
      {showBidButton && (
        <Button
          variant="default"
          onClick={onBid}
          className="rounded-full bg-gradient-primary hover:opacity-90 border-0"
        >
          Bid: {currentBid ? formatBid(currentBid) : '---'}
        </Button>
      )}
    </Card>
  );
};
