import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { SquadRow } from "@/components/SquadRow";
import { Loader2 } from "lucide-react";
import { fetchAvailableSubs, setLineup } from "@/lib/api";

interface Substitute {
  id: number;
  name: string;
  value: number;
  totalPoints: number;
  averagePoints: number;
}

interface SubstitutesDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  playerId?: string;
  position: number;
  currentFootballerId?: number;
  onSwapComplete?: () => void;
}

export const SubstitutesDialog = ({
  open,
  onOpenChange,
  playerId,
  position,
  currentFootballerId,
  onSwapComplete,
}: SubstitutesDialogProps) => {
  const [substitutes, setSubstitutes] = useState<Substitute[]>([]);
  const [loading, setLoading] = useState(true);
  const [swapping, setSwapping] = useState(false);

  useEffect(() => {
    if (open) {
      if (!playerId) {
        setSubstitutes([]);
        setLoading(false);
        return;
      }

      setLoading(true);
      fetchAvailableSubs(playerId, position)
        .then((data) => {
          setSubstitutes(data);
        })
        .catch((error) => {
          console.error("Error fetching substitutes:", error);
          setSubstitutes([]);
        })
        .finally(() => {
          setLoading(false);
        });
    }
  }, [open, playerId, position]);

  const handleSubstituteClick = async (newFootballerId: number) => {
    if (swapping) return;
    
    setSwapping(true);
    try {
      // Only remove current footballer if one exists (swapping)
      if (currentFootballerId) {
        await setLineup(playerId, currentFootballerId, false);
      }
      // Add new footballer to lineup
      await setLineup(playerId, newFootballerId, true);
      
      onSwapComplete?.();
      onOpenChange(false);
    } catch (error) {
      console.error("Error updating lineup:", error);
    } finally {
      setSwapping(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
        <DialogHeader>
          <DialogTitle>Available Substitutes</DialogTitle>
        </DialogHeader>

        {loading ? (
          <div className="flex justify-center items-center py-12">
            <Loader2 className="h-8 w-8 animate-spin text-primary" />
          </div>
        ) : substitutes.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">
            No substitutes available
          </div>
        ) : (
          <div className="overflow-auto flex-1">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Player</TableHead>
                  <TableHead className="text-center">Total Pts</TableHead>
                  <TableHead className="text-center">Avg Pts</TableHead>
                  <TableHead className="text-center">Value</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {substitutes.map((sub) => (
                  <SquadRow
                    key={sub.id}
                    id={sub.id}
                    name={sub.name}
                    value={sub.value}
                    totalPoints={sub.totalPoints}
                    averagePoints={sub.averagePoints}
                    onClick={() => handleSubstituteClick(sub.id)}
                  />
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
};
