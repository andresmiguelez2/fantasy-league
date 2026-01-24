import { TableCell, TableRow } from "@/components/ui/table";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface PlayerRowProps {
  playerId: number;
  name: string;
  points: number;
  team_value: number;
  onPlayerClick?: (playerId: number, name: string) => void;
}

export const PlayerRow = ({ playerId, name, points, team_value, onPlayerClick }: PlayerRowProps) => {
  const formatValue = (val: number) => {
    return new Intl.NumberFormat('en-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(val);
  };
  
  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };
  
  const handleClick = () => {
    if (onPlayerClick) {
      onPlayerClick(playerId, name);
    }
  };
  
  return (
    <TableRow className="fade-in cursor-pointer hover:bg-accent/10 transition-colors" onClick={handleClick}>
      <TableCell className="flex items-center gap-3">
        <Avatar className="h-10 w-10 border-2 border-secondary/30">
          <AvatarImage src={`https://api.dicebear.com/7.x/avataaars/svg?seed=${name}`} />
          <AvatarFallback className="bg-gradient-primary text-white font-semibold text-sm">
            {getInitials(name)}
          </AvatarFallback>
        </Avatar>
        <span className="font-semibold">{name}</span>
      </TableCell>
      <TableCell className="text-center">
        <span className="text-accent font-semibold">{points} pts</span>
      </TableCell>
      <TableCell className="text-center">
        <span className="text-secondary font-semibold">{formatValue(team_value)}</span>
      </TableCell>
    </TableRow>
  );
};
