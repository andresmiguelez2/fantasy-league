import { useState, useEffect } from "react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { fetchReleaseClauseData } from "@/lib/api";

interface ReleaseClauseDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  footballerName: string;
  footballerId: number;
  onSubmit: () => void;
}

interface ReleaseClauseData {
  status: string;
  rc_available: boolean;
  release_clause: number;
  time_until_rc?: number;
}

export const ReleaseClauseDialog = ({
  open,
  onOpenChange,
  footballerName,
  footballerId,
  onSubmit,
}: ReleaseClauseDialogProps) => {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<ReleaseClauseData | null>(null);
  
  useEffect(() => {
    if (open && footballerId) {
      setLoading(true);
      fetchReleaseClauseData(footballerId)
        .then(data => {
          setData(data);
          setLoading(false);
        })
        .catch(err => {
          console.error(err);
          setLoading(false);
        });
    }
  }, [open, footballerId]);
  
  const handleSubmit = () => {
    onSubmit();
    onOpenChange(false);
  };
  
  const formatValue = (val: number) => {
    return new Intl.NumberFormat('en-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(val);
  };
  
  const formatTimeRemaining = (seconds: number | undefined) => {
    // Return empty string if undefined, zero, or negative
    if (seconds === undefined || seconds <= 0) return '';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    // Format as DD hh:mm:ss
    const hh = hours.toString().padStart(2, '0');
    const mm = minutes.toString().padStart(2, '0');
    const ss = secs.toString().padStart(2, '0');
    
    return `${days} ${hh}:${mm}:${ss}`;
  };
  
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Pay Release Clause</DialogTitle>
          <DialogDescription>
            Release clause for {footballerName}
          </DialogDescription>
        </DialogHeader>
        
        {loading ? (
          <div className="py-4 text-center text-muted-foreground">
            Loading release clause data...
          </div>
        ) : data ? (
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <div className="text-sm text-muted-foreground">Release Clause Amount:</div>
              <div className="text-2xl font-bold text-primary">
                {formatValue(data.release_clause)}
              </div>
            </div>
            
            {!data.rc_available && (
              <div className="space-y-2">
                <div className="text-sm text-destructive">
                  Release clause is not available for this footballer.
                </div>
                {data.time_until_rc !== undefined && data.time_until_rc > 0 && (
                  <div className="text-sm text-muted-foreground">
                    Time remaining: <span className="font-semibold" aria-label="Days hours minutes seconds">{formatTimeRemaining(data.time_until_rc)}</span>
                    <div className="text-xs mt-1 opacity-75">(days hh:mm:ss)</div>
                  </div>
                )}
              </div>
            )}
          </div>
        ) : (
          <div className="py-4 text-center text-destructive">
            Failed to load release clause data.
          </div>
        )}
        
        <DialogFooter className="flex-col sm:flex-row gap-2">
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Cancel
          </Button>
          <Button 
            onClick={handleSubmit}
            disabled={loading || !data || !data.rc_available}
          >
            Pay Release Clause
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
