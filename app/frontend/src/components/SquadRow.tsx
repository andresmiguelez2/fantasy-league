import { TableCell, TableRow } from "@/components/ui/table";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface SquadRowProps {
  id: number;
  name: string;
  value: number;
  totalPoints: number;
  averagePoints: number | string;
  onClick?: () => void;
}

export const SquadRow = ({ id, name, value, totalPoints, averagePoints, onClick }: SquadRowProps) => {
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
  
  return (
    <TableRow className="fade-in cursor-pointer hover:bg-accent/50" onClick={onClick}>
      <TableCell className="flex items-center gap-3">
        <Avatar className="h-14 w-14 border-2 border-secondary/30">
          <AvatarImage src={`${import.meta.env.VITE_BACKEND_URL}/footballer/image/${id}`} />
          <AvatarFallback className="bg-gradient-primary text-white font-semibold text-sm">
            {getInitials(name)}
          </AvatarFallback>
        </Avatar>
        <span className="font-semibold">{name}</span>
      </TableCell>
      <TableCell className="text-center">
        <span className="font-semibold text-green-600">{totalPoints}</span>
      </TableCell>
      <TableCell className="text-center">
        <span className="font-semibold">{averagePoints}</span>
      </TableCell>
      <TableCell className="text-center">
        <span className="text-secondary font-semibold">{formatValue(value)}</span>
      </TableCell>
    </TableRow>
  );
};
