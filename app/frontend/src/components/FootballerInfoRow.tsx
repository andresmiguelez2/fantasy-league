import { TableCell, TableRow } from "@/components/ui/table";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";

interface FootballerInfoRowProps {
  id: number;
  name: string;
  value: number;
  ownerId: string;
  averagePoints: number | string;
  totalPoints: number;
  onClick?: () => void;
}

export const FootballerInfoRow = ({ 
  id, 
  name, 
  value, 
  ownerId,
  averagePoints,
  totalPoints,
  onClick 
}: FootballerInfoRowProps) => {
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
        <div className="flex flex-col">
          <span className="font-semibold">{name}</span>
          {ownerId && <span className="text-xs text-muted-foreground">Owner: {ownerId}</span>}
        </div>
      </TableCell>
      <TableCell className="text-center">
        <span className="text-secondary font-semibold">{formatValue(value)}</span>
      </TableCell>
      <TableCell className="text-center">
        <span className="font-semibold">{totalPoints}</span>
      </TableCell>
      <TableCell className="text-center">
        <span className="font-semibold">{averagePoints}</span>
      </TableCell>
    </TableRow>
  );
};
