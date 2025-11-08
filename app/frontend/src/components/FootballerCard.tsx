import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface FootballerCardProps {
  id: number;
  name: string;
  owner?: string;        // renamed to avoid confusion
  currentBid?: number;
  showBidButton?: boolean;
  onBid?: () => void;
  onOwnerClick?: () => void; // optional handler for owner button
}

export const FootballerCard = ({
  id,
  name,
  owner,
  currentBid,
  showBidButton = false,
  onBid,
  onOwnerClick,
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
       <div className="flex items-center gap-3">
         <Avatar className="h-14 w-14 border-2 border-secondary/30">
           <AvatarImage src={`${import.meta.env.VITE_BACKEND_URL}/images/${id}`} />
           <AvatarFallback className="bg-gradient-primary text-white font-semibold text-sm">
             {getInitials(name)}
           </AvatarFallback>
         </Avatar>
         <div>
           <span className="font-semibold text-foreground">{name}</span>
           {owner ? <div className="text-sm text-secondary">{owner}</div> : null}
         </div>
       </div>
      <div className="flex items-center gap-2">
        {showBidButton && (
          <Button
            variant="default"
            onClick={onBid}
            className="rounded-full bg-gradient-primary hover:opacity-90 border-0"
          >
            {currentBid ? `Bid: ${formatBid(currentBid)}` : "Bid: ---"}
          </Button>
        )}
      </div>
     </Card>
   );
 };
