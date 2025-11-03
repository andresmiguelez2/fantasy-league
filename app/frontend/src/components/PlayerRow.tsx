import { TableCell, TableRow } from "@/components/ui/table";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface PlayerRowProps {
  name: string;
  points: number;
  value: number;
}

export const PlayerRow = ({ name, points, value }: PlayerRowProps) => {
  const formatValue = (val: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(val);
  };
  
  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };
  
  return (
    <TableRow className="fade-in">
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
        <span className="text-secondary font-semibold">{formatValue(value)}</span>
      </TableCell>
    </TableRow>
  );
};
