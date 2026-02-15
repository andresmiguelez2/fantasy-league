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
      fetch(`${import.meta.env.VITE_BACKEND_URL}/footballer/release_clause_data/${footballerId}`)
        .then(res => res.json())
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
  
  const pluralize = (count: number, singular: string) => {
    return `${count} ${singular}${count !== 1 ? 's' : ''}`;
  };
  
  const formatTimeRemaining = (seconds: number | undefined) => {
    if (seconds === undefined) return '';
    
    // If negative or zero, release clause is already available
    if (seconds <= 0) return '';
    
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const secs = Math.floor(seconds % 60);
    
    if (days > 0) {
      const hoursText = hours > 0 ? ` ${pluralize(hours, 'hour')}` : '';
      return `${pluralize(days, 'day')}${hoursText}`;
    } else if (hours > 0) {
      const minutesText = minutes > 0 ? ` ${pluralize(minutes, 'minute')}` : '';
      return `${pluralize(hours, 'hour')}${minutesText}`;
    } else if (minutes > 0) {
      return pluralize(minutes, 'minute');
    } else {
      return pluralize(secs, 'second');
    }
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
                    Time remaining: <span className="font-semibold">{formatTimeRemaining(data.time_until_rc)}</span>
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
