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
      notation: 'compact',
      maximumFractionDigits: 2,
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
      <div className="flex flex-col gap-2 sm:grid sm:grid-cols-[minmax(0,2.2fr)_72px_88px_78px_96px] sm:gap-3 sm:items-center">
        {/* Row 1 (mobile) / Column 1 (sm+): avatar + name */}
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

        {/* Row 2 (mobile): compact 4-col strip. On sm+, `contents` hands these off as columns 2-5 of the parent grid */}
        <div className="grid grid-cols-[44px_1fr_1fr_88px] gap-2 items-center sm:contents">
          <div className="flex flex-col items-center gap-0.5 sm:flex-row sm:justify-center sm:gap-1">
            {positionStyle ? (
              <span className={`inline-block px-1.5 py-0.5 rounded text-[10px] sm:text-xs font-bold uppercase ${positionStyle.className}`}>
                {positionStyle.label}
              </span>
            ) : (
              <span className="text-muted-foreground text-xs">{position ?? "—"}</span>
            )}
            <AvailabilityIcon availability={availability} />
          </div>

          <div className="text-center">
            <div className="text-[10px] text-muted-foreground sm:hidden">Value</div>
            <div className="text-xs sm:text-sm font-semibold text-foreground">
              {value !== undefined ? formatMoney(value) : "—"}
            </div>
          </div>

          <div className="text-center">
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

          <div className="text-center">
            {showBidButton ? (
              <div className="space-y-1">
                <div className="text-xs sm:text-sm font-semibold text-foreground min-h-5">
                  {currentBid !== undefined ? formatMoney(currentBid) : "—"}
                </div>
                <Button
                  variant="default"
                  onClick={onBid}
                  className="w-full rounded-full bg-gradient-primary hover:opacity-90 border-0 text-xs sm:text-sm px-2 sm:px-4 h-7 sm:h-10"
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
      </div>
    </Card>
  );
};