import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { BACKEND_URL } from "@/lib/api";
import { AvailabilityIcon } from "@/components/AvailabilityIcon";

const POSITION_STYLES: Record<string, { label: string; className: string }> = {
  gk:  { label: "GK",  className: "bg-yellow-400 text-yellow-900" },
  df: { label: "DF", className: "bg-blue-500 text-white" },
  md: { label: "MD", className: "bg-green-500 text-white" },
  fw: { label: "FW", className: "bg-red-500 text-white" },
};

interface FootballerCardProps {
  id: number;
  name: string;
  owner?: string;
  value?: number;
  currentBid?: number;
  showBidButton?: boolean;
  onBid?: () => void;
  onOwnerClick?: () => void;
  totalPoints?: number;
  averagePoints?: number | string;
  position?: string | null;
  availability?: string | null;
}

export const FootballerCard = ({
  id,
  name,
  owner,
  value,
  currentBid,
  showBidButton = false,
  onBid,
  onOwnerClick,
  totalPoints,
  averagePoints,
  position,
  availability,
}: FootballerCardProps) => {
  const formatMoney = (amount: number) => {
     return new Intl.NumberFormat('en-ES', {
       style: 'currency',
       currency: 'EUR',
       minimumFractionDigits: 0,
       maximumFractionDigits: 0,
     }).format(amount);
   };
   
   const getInitials = (name?: string | null) => {
     const safe = name?.trim();
     if (!safe) return "?";
     return safe
       .split(/\s+/)
       .map((part) => part[0])
       .join("")
       .toUpperCase()
       .slice(0, 2);
   };
   
  const positionKey = position?.toLowerCase() ?? "";
  const positionStyle = POSITION_STYLES[positionKey];

  return (
    <Card className="p-3 sm:p-4 fade-in hover-lift border-primary/20 bg-gradient-to-r from-card to-card/80">
      <div className="grid grid-cols-[minmax(0,2.2fr)_72px_88px_78px_96px] gap-3 items-center">
        <div className="flex items-center gap-2 sm:gap-3 min-w-0 cursor-pointer" onClick={() => onOwnerClick?.()}>
          <Avatar className="h-10 w-10 sm:h-14 sm:w-14 border-2 border-secondary/30 flex-shrink-0">
            <AvatarImage src={`${BACKEND_URL}/footballer/image/${id}`} />
            <AvatarFallback className="bg-gradient-primary text-white font-semibold text-xs sm:text-sm">
              {getInitials(name)}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0 flex-1">
            <span className="font-semibold text-foreground text-sm sm:text-base block truncate">{name}</span>
            {owner ? <div className="text-xs sm:text-sm text-secondary truncate">{owner}</div> : null}
          </div>
        </div>

        <div className="text-center flex-shrink-0">
          <div className="flex items-center justify-center gap-1">
            {positionStyle ? (
              <span className={`inline-block px-2 py-0.5 rounded text-xs font-bold uppercase ${positionStyle.className}`}>
                {positionStyle.label}
              </span>
            ) : (
              <span className="text-muted-foreground text-xs">{position ?? "—"}</span>
            )}
            <AvailabilityIcon availability={availability} />
          </div>
        </div>

        <div className="text-center flex-shrink-0">
          <div className="text-xs sm:text-sm font-semibold text-foreground">
            {value !== undefined ? formatMoney(value) : "—"}
          </div>
        </div>

        <div className="text-center flex-shrink-0">
          {(totalPoints !== undefined || averagePoints !== undefined) ? (
            <div>
              <div className="text-xs sm:text-sm font-semibold text-foreground">
                {totalPoints ?? 0}
              </div>
              <div className="text-[10px] sm:text-xs text-muted-foreground">
                {averagePoints ?? '0'}
              </div>
            </div>
          ) : (
            <span className="text-muted-foreground text-xs">—</span>
          )}
        </div>

        <div className="text-center flex-shrink-0">
          {showBidButton ? (
            <div className="space-y-1">
              <div className="text-xs sm:text-sm font-semibold text-foreground min-h-5">
                {currentBid !== undefined ? formatMoney(currentBid) : "—"}
              </div>
              <Button
                variant="default"
                onClick={onBid}
                className="w-full rounded-full bg-gradient-primary hover:opacity-90 border-0 text-xs sm:text-sm px-2 sm:px-4 h-8 sm:h-10"
              >
                Bid
              </Button>
            </div>
          ) : (
            <div className="text-xs sm:text-sm font-semibold text-foreground min-h-5">
              {currentBid !== undefined ? formatMoney(currentBid) : "—"}
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};
