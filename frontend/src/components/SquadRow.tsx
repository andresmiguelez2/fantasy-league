import { TableCell, TableRow } from "@/components/ui/table";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { BACKEND_URL } from "@/lib/api";
import { AvailabilityIcon } from "@/components/AvailabilityIcon";

interface SquadRowProps {
  id: number;
  name: string;
  value: number;
  totalPoints: number;
  averagePoints: number | string;
  position?: string | null;
  availability?: string | null;
  onClick?: () => void;
}

const POSITION_STYLES: Record<string, { label: string; className: string }> = {
  gk: { label: "GK", className: "bg-yellow-400 text-yellow-900" },
  df: { label: "DF", className: "bg-blue-500 text-white" },
  md: { label: "MD", className: "bg-green-500 text-white" },
  fw: { label: "FW", className: "bg-red-500 text-white" },
};

export const SquadRow = ({
  id,
  name,
  value,
  totalPoints,
  averagePoints,
  position,
  availability,
  onClick,
}: SquadRowProps) => {
  const formatValue = (val: number) => {
    return new Intl.NumberFormat("en-ES", {
      style: "currency",
      currency: "EUR",
      notation: "compact",
      maximumFractionDigits: 2,
    }).format(val);
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
    <TableRow className="fade-in cursor-pointer hover:bg-accent/50" onClick={onClick}>
      <TableCell className="flex items-center gap-3">
        <Avatar className="h-14 w-14 border-2 border-secondary/30">
          <AvatarImage src={`${BACKEND_URL}/footballer/image/${id}`} />
          <AvatarFallback className="bg-gradient-primary text-white font-semibold text-sm">
            {getInitials(name)}
          </AvatarFallback>
        </Avatar>
        <span className="font-semibold">{name}</span>
      </TableCell>
      <TableCell className="text-center">
        {positionStyle ? (
          <span
            className={`inline-block px-2 py-0.5 rounded text-xs font-bold uppercase ${positionStyle.className}`}
          >
            {positionStyle.label}
          </span>
        ) : (
          <span className="text-muted-foreground text-xs">{position ?? "—"}</span>
        )}
      </TableCell>
      <TableCell className="text-center">
        <AvailabilityIcon availability={availability} />
      </TableCell>
      <TableCell className="text-center">
        <div className="text-sm font-semibold text-foreground">{totalPoints ?? 0}</div>
        <div className="text-xs text-muted-foreground">{averagePoints ?? "0"}</div>
      </TableCell>
      <TableCell className="text-center">
        <span className="text-secondary font-semibold">{formatValue(value)}</span>
      </TableCell>
    </TableRow>
  );
};
