import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface FootballerCardProps {
  id: number;
  name: string;
  owner?: string;
  currentBid?: number;
  showBidButton?: boolean;
  onBid?: () => void;
  onOwnerClick?: () => void;
  totalPoints?: number;
  averagePoints?: number | string;
}

export const FootballerCard = ({
  id,
  name,
  owner,
  currentBid,
  showBidButton = false,
  onBid,
  onOwnerClick,
  totalPoints,
  averagePoints,
}: FootballerCardProps) => {
   const formatBid = (amount: number) => {
     return new Intl.NumberFormat('en-ES', {
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
      {/* Left: avatar + fixed-width name column so text boxes align vertically */}
      <div className="flex items-center gap-3 cursor-pointer" onClick={() => onOwnerClick?.()}>
        <Avatar className="h-14 w-14 border-2 border-secondary/30">
          <AvatarImage src={`${import.meta.env.VITE_BACKEND_URL}/footballer/image/${id}`} />
          <AvatarFallback className="bg-gradient-primary text-white font-semibold text-sm">
            {getInitials(name)}
          </AvatarFallback>
        </Avatar>
        <div className="min-w-[12rem]">
          <span className="font-semibold text-foreground">{name}</span>
          {owner ? <div className="text-sm text-secondary">{owner}</div> : null}
        </div>
      </div>

      {/* Center: stats with fixed width to align across cards */}
      <div className="w-28 text-center">
        {(totalPoints !== undefined || averagePoints !== undefined) && (
          <div>
            <div className="text-sm font-semibold text-foreground">
              {totalPoints ?? 0} pts
            </div>
            <div className="text-xs text-muted-foreground">
              Avg: {averagePoints || '0'}
            </div>
          </div>
        )}
      </div>

      {/* Right: Bid button - fixed width so it doesn't shift center stats */}
      <div className="w-32 flex items-center justify-end">
        {showBidButton && (
          <Button
            variant="default"
            onClick={onBid}
            className="w-full rounded-full bg-gradient-primary hover:opacity-90 border-0 truncate"
          >
            {currentBid ? `Bid: ${formatBid(currentBid)}` : "Bid: ---"}
          </Button>
        )}
      </div>
     </Card>
   );
 };
