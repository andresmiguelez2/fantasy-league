import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { BidDialog } from "@/components/BidDialog";
import { ReleaseClauseDialog } from "@/components/ReleaseClauseDialog";
import { IncrementReleaseClauseDialog } from "@/components/IncrementReleaseClauseDialog";
import { AvailabilityIcon } from "@/components/AvailabilityIcon";
import { fetchFootballerInfo, fetchFixtureDetail, FootballerInfo, FixtureDetail, placeBid, payReleaseClause, scheduleReleaseClauseBid, fetchMarketStatus, changeMarketStatus, getActivePlayerId, BACKEND_URL, incrementReleaseClause, fetchReleaseClauseData } from "@/lib/api";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Brush, Cell } from "recharts";
import { MoreVertical } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { useParams } from "react-router-dom";

interface FootballerInfoDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  footballerId: number;
  footballerName?: string;
  defaultFixture?: number | null;
  ownerId?: string | null;
  onBid?: () => void;
}

export const FootballerInfoDialog = ({
  open,
  onOpenChange,
  footballerId,
  footballerName,
  defaultFixture,
  ownerId,
  onBid,
}: FootballerInfoDialogProps) => {
  const [info, setInfo] = useState<FootballerInfo | null>(null);
  const [releaseClauseRemainingSeconds, setReleaseClauseRemainingSeconds] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [imgError, setImgError] = useState(false);
  const [teamBadgeError, setTeamBadgeError] = useState(false);
  const [selectedFixture, setSelectedFixture] = useState<number | null>(null);
  const [fixtureDetail, setFixtureDetail] = useState<FixtureDetail | null>(null);
  const [bidDialogOpen, setBidDialogOpen] = useState(false);
  const [releaseClauseDialogOpen, setReleaseClauseDialogOpen] = useState(false);
  const [incrementReleaseClauseDialogOpen, setIncrementReleaseClauseDialogOpen] = useState(false);
  const [onMarket, setOnMarket] = useState<boolean | null>(null);
  const [releaseClause, setReleaseClause] = useState<number | null>(null);
  const { toast } = useToast();
  const { playerId } = useParams();

  useEffect(() => {
    if (open) {
      setLoading(true);
      setSelectedFixture(null);
      setFixtureDetail(null);
      setTeamBadgeError(false);
      fetchFootballerInfo(footballerId)
        .then(setInfo)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [open, footballerId]);

  // Fetch market status when the dialog opens (for owned footballers)
  useEffect(() => {
    if (open && footballerId) {
      fetchMarketStatus(footballerId)
        .then(setOnMarket)
        .catch(console.error);
    }
  }, [open, footballerId]);

  useEffect(() => {
    if (open && footballerId) {
      fetchReleaseClauseData(footballerId)
        .then((data) => setReleaseClause(data.release_clause))
        .catch(console.error);
    }
  }, [open, footballerId]);

  // Set default fixture to provided value or latest when info loads
  useEffect(() => {
    if (info && info.fixture_breakdown.length > 0) {
      if (defaultFixture !== undefined && defaultFixture !== null) {
        setSelectedFixture(defaultFixture);
      } else {
        const latestFixture = Math.max(...info.fixture_breakdown.map(f => f.fixture));
        setSelectedFixture(latestFixture);
      }
    }
  }, [info, defaultFixture]);

  // Fetch fixture detail when selected fixture changes
  useEffect(() => {
    if (selectedFixture !== null && footballerId) {
      fetchFixtureDetail(footballerId, selectedFixture)
        .then(setFixtureDetail)
        .catch(console.error);
    }
  }, [selectedFixture, footballerId]);

  useEffect(() => {
    if (!info) {
      setReleaseClauseRemainingSeconds(null);
      return;
    }

    // Backend sends negative seconds while release clause is still blocked.
    if (info.time_to_release_clause === null || info.time_to_release_clause >= 0) {
      setReleaseClauseRemainingSeconds(null);
      return;
    }

    setReleaseClauseRemainingSeconds(Math.ceil(Math.abs(info.time_to_release_clause)));
  }, [info]);

  useEffect(() => {
    if (releaseClauseRemainingSeconds === null) {
      return;
    }

    const intervalId = window.setInterval(() => {
      setReleaseClauseRemainingSeconds((current) => {
        if (current === null || current <= 1) {
          return null;
        }

        return current - 1;
      });
    }, 1000);

    return () => window.clearInterval(intervalId);
  }, [releaseClauseRemainingSeconds]);

  const formatValue = (val: number) => {
    return new Intl.NumberFormat('en-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
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

  const formatReleaseClauseCountdown = (seconds: number) => {
    const days = Math.floor(seconds / 86400);
    const hours = Math.floor((seconds % 86400) / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    const remainingSeconds = seconds % 60;

    const paddedDays = String(days).padStart(2, "0");
    const paddedHours = String(hours).padStart(2, "0");
    const paddedMinutes = String(minutes).padStart(2, "0");
    const paddedSeconds = String(remainingSeconds).padStart(2, "0");

    return `${paddedDays}d ${paddedHours}h ${paddedMinutes}m ${paddedSeconds}s`;
  };

  const handleBarClick = (data: any) => {
    if (data && data.activePayload && data.activePayload[0]) {
      setSelectedFixture(data.activePayload[0].payload.fixture);
    }
  };

  const getCurrentPlayerId = () => {
    return playerId || getActivePlayerId();
  };

  const extractMessage = (resp: any) => {
    return resp?.message || resp?.detail || resp?.text || 
           (typeof resp === 'string' ? resp : JSON.stringify(resp));
  };

  const handleBidSubmit = async (amount: number, timestamp?: string | null) => {
    if (!info) return false;
    
    const id = getCurrentPlayerId();
    if (!id) {
      toast({
        description: "Unable to place bid: player ID not found",
        variant: "destructive",
      });
      return false;
    }
    
    const resp = await placeBid(footballerId, id, amount, timestamp);
    const message = extractMessage(resp);
    const scheduledForFuture = timestamp && new Date(timestamp).getTime() > Date.now();

    toast({
      description: message || (amount === 0
        ? `Your bid for ${info.name} has been deleted.`
        : scheduledForFuture
          ? `Your bid of €${amount.toLocaleString()} for ${info.name} has been scheduled.`
          : `Your bid of €${amount.toLocaleString()} for ${info.name} has been placed.`),
      variant: resp?.status === "success" ? "default" : "destructive",
    });

    return resp?.status === "success";
  };

  const handleReleaseClauseSubmit = async () => {
    if (!info) return false;
    
    const id = getCurrentPlayerId();
    if (!id) {
      toast({
        description: "Unable to pay release clause: player ID not found",
        variant: "destructive",
      });
      return false;
    }
    
    const resp = await payReleaseClause(footballerId, id);
    const message = extractMessage(resp);

    toast({
      description: message || `Release clause paid for ${info.name}.`,
      variant: resp?.status === "success" ? "default" : "destructive",
    });

    if (resp?.status === "success") {
      // Refresh info after successful transfer
      fetchFootballerInfo(footballerId)
        .then(setInfo)
        .catch(console.error);
    }
    return resp?.status === "success";
  };

  const handleScheduleReleaseClauseBidSubmit = async (amount: number) => {
    if (!info) return false;

    const id = getCurrentPlayerId();
    if (!id) {
      toast({
        description: "Unable to schedule release clause bid: player ID not found",
        variant: "destructive",
      });
      return false;
    }

    const resp = await scheduleReleaseClauseBid(footballerId, id, amount);
    const message = extractMessage(resp);
    toast({
      description: message || `Release clause bid for ${info.name} has been scheduled.`,
      variant: resp?.status === "success" ? "default" : "destructive",
    });
    return resp?.status === "success";
  };

  // Check if "Offer Amount" and "Pay release clause" options should be available
  // Only available if the footballer belongs to another player (not NULL and not current player)
  const canPlaceBid = info?.owner_id !== null && 
                      info?.owner_id?.toString() !== getCurrentPlayerId();

  // Check if the current player owns this footballer
  const isOwner = info?.owner_id?.toString() === getCurrentPlayerId();

  const handleMarketStatusToggle = async () => {
    const newStatus = !onMarket;
    try {
      const resp = await changeMarketStatus(footballerId, newStatus);
      if (resp?.status === "success") {
        setOnMarket(newStatus);
        toast({
          description: newStatus
            ? `${info?.name} has been placed on the market.`
            : `${info?.name} has been removed from the market.`,
        });
      } else {
        toast({
          description: resp?.message || "Failed to update market status.",
          variant: "destructive",
        });
      }
    } catch {
      toast({
        description: "Failed to update market status.",
        variant: "destructive",
      });
    }
  };

  const handleIncrementReleaseClause = async (increment: number) => {
    const id = getCurrentPlayerId();
    if (!id) {
      toast({
        description: "Unable to increment release clause: player ID not found",
        variant: "destructive",
      });
      return false;
    }

    const resp = await incrementReleaseClause(footballerId, id, increment);
    const message = extractMessage(resp);
    toast({
      description: message || `Release clause updated for ${info?.name}.`,
      variant: resp?.status === "success" ? "default" : "destructive",
    });
    return resp?.status === "success";
  };

  if (loading || !info) {
    return (
      <Dialog open={open} onOpenChange={onOpenChange}>
        <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>Loading...</DialogTitle>
          </DialogHeader>
        </DialogContent>
      </Dialog>
    );
  }

  const sortedFixtures = [...info.fixture_breakdown].sort((a, b) => a.fixture - b.fixture);
  const yTicks = Array.from({ length: Math.floor(15 / 3) + 1 }, (_, i) => i * 3);
  const initialStartIndex = Math.max(0, sortedFixtures.length - 5);
  const initialEndIndex = Math.max(0, sortedFixtures.length - 1);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="sr-only">Footballer Information</DialogTitle>
        </DialogHeader>

        {/* Top Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <Card className="p-6 flex items-center justify-center w-full">
            <div className="h-48 w-full max-w-md border-4 border-secondary/30 overflow-hidden flex items-center justify-center bg-background">
              {!imgError ? (
                <img
                  src={`${BACKEND_URL}/footballer/image/${footballerId}`}
                  alt={info.name}
                  className="max-h-full max-w-full object-contain object-center"
                  onError={() => setImgError(true)}
                />
              ) : (
                <div className="h-full w-full bg-gradient-primary text-white font-semibold text-4xl flex items-center justify-center">
                  {getInitials(info.name)}
                </div>
              )}
            </div>
          </Card>

          <div className="space-y-4">
            <Card className="p-4">
              <div className="flex items-center gap-3">
                {!teamBadgeError && (
                  <img
                    src={`${BACKEND_URL}/team/image/${encodeURIComponent(info.team)}`}
                    alt={`${info.team} team badge`}
                    className="w-10 self-stretch object-contain flex-shrink-0"
                    onError={() => setTeamBadgeError(true)}
                  />
                )}
                <div className="flex-1 text-center">
                  <h3 className="text-2xl font-bold">{info.name}</h3>
                  {info.owner_name != null && (
                    <p className="text-sm text-muted-foreground mt-1">{info.owner_name}</p>
                  )}
                </div>
              </div>
            </Card>

            <Card className="p-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Total Points</p>
                  <p className="text-2xl font-bold text-primary">{info.total_points}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Average Points</p>
                  <p className="text-2xl font-bold text-secondary">{info.average_points.toFixed(2)}</p>
                </div>
              </div>
            </Card>

            {(info.position || info.availability || info.time_to_release_clause !== null) && (
              <Card className="p-4">
                <div className="flex items-center justify-between">
                  {info.position && (
                    <div className="w-14 flex-shrink-0">
                      <p className="text-sm font-semibold uppercase truncate">{info.position}</p>
                    </div>
                  )}
                  <div className="flex items-center gap-6 ml-auto">
                    {info.availability && (
                      <div className="w-20 flex-shrink-0 flex justify-center">
                        <AvailabilityIcon availability={info.availability} showText />
                      </div>
                    )}
                    <div className="w-36 flex-shrink-0 text-right">
                      <p className="text-sm text-muted-foreground">Release Clause</p>
                      <p className="text-sm font-semibold truncate">
                        {releaseClauseRemainingSeconds === null
                          ? "Available"
                          : formatReleaseClauseCountdown(releaseClauseRemainingSeconds)}
                      </p>
                    </div>
                  </div>
                </div>
              </Card>
            )}

            <Card className="p-4">
              <div className="flex items-start justify-between">
                <div className="flex-1 flex gap-6">
                  <div>
                    <p className="text-sm text-muted-foreground">Market Value</p>
                    <p className="text-2xl font-bold text-accent">{formatValue(info.market_value)}</p>
                  </div>
                  {releaseClause !== null && (
                    <div>
                      <p className="text-sm text-muted-foreground">Release Clause</p>
                      <p className="text-2xl font-bold text-destructive">{formatValue(releaseClause)}</p>
                    </div>
                  )}
                </div>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                      <MoreVertical className="h-4 w-4" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    {canPlaceBid && (
                      <DropdownMenuItem onClick={() => setBidDialogOpen(true)}>
                        Offer Amount
                      </DropdownMenuItem>
                    )}
                    {canPlaceBid && (
                      <DropdownMenuItem onClick={() => setReleaseClauseDialogOpen(true)}>
                        Pay release clause
                      </DropdownMenuItem>
                    )}
                    {isOwner && onMarket !== null && (
                      <DropdownMenuItem onClick={handleMarketStatusToggle}>
                        {onMarket ? "Remove from market" : "Place on market"}
                      </DropdownMenuItem>
                    )}
                    {isOwner && (
                      <DropdownMenuItem onClick={() => setIncrementReleaseClauseDialogOpen(true)}>
                        Increment release clause
                      </DropdownMenuItem>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              </div>
            </Card>
          </div>
        </div>

        {/* Fixture Breakdown Bar Chart */}
        <Card className="p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Points by Fixture {selectedFixture && <span className="text-muted-foreground text-sm"></span>}</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={sortedFixtures} onClick={handleBarClick}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="fixture" 
                label={{ value: 'Fixture', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                label={{ value: 'Points', angle: -90, position: 'insideLeft' }}
                domain={[0, 15]}
                ticks={yTicks}
              />
              <Tooltip />
              <Brush dataKey="fixture" height={30} stroke="hsl(var(--primary))" startIndex={initialStartIndex} endIndex={initialEndIndex} travellerWidth={10} />
              <Bar dataKey="points" cursor="pointer">
                {sortedFixtures.map((entry) => (
                  <Cell
                    key={`cell-${entry.fixture}`}
                    fill={entry.fixture === selectedFixture ? "hsl(var(--accent))" : "hsl(var(--primary))"}
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </Card>

        {/* Fixture Detail Table */}
        {fixtureDetail && (
          <Card className="p-6 mb-6">
            <h3 className="text-lg font-semibold mb-4">Fixture {fixtureDetail.fixture} Breakdown</h3>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Item</TableHead>
                  <TableHead className="text-center">Value</TableHead>
                  <TableHead className="text-center">Points</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {Object.entries(fixtureDetail.breakdown).map(([item, data]) => (
                  <TableRow key={item}>
                    <TableCell>{item}</TableCell>
                    <TableCell className="text-center">{(data as { value: number | null; points: number }).value ?? '-'}</TableCell>
                    <TableCell className="text-center text-primary font-semibold">{(data as { value: number | null; points: number }).points}</TableCell>
                  </TableRow>
                ))}
                <TableRow className="bg-green-600/10 border-t-2 border-green-600">
                  <TableCell className="font-bold">Total</TableCell>
                  <TableCell className="text-center">-</TableCell>
                  <TableCell className="text-center text-green-600 font-bold text-lg">
                    {Object.values(fixtureDetail.breakdown).reduce((sum, data) => sum + (data as { value: number | null; points: number }).points, 0)}
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </Card>
        )}

        {/* Market Value Line Chart */}
        <Card className="p-6 mb-4">
          <h3 className="text-lg font-semibold mb-4">Market Value History</h3>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={info.market_details}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="date" 
                label={{ value: 'Date', position: 'insideBottom', offset: -5 }}
                tick={{ fontSize: 12 }}
                interval="preserveStartEnd"
              />
              <YAxis 
                label={{ value: 'Value (€)', angle: -90, position: 'insideLeft' }}
                tickFormatter={(value) => `€${(value / 1000000).toFixed(1)} M`}
              />
              <Tooltip 
                formatter={(value: number) => formatValue(value)}
                labelStyle={{ color: 'hsl(var(--foreground))' }}
              />
              <Line 
                type="monotone" 
                dataKey="value" 
                stroke="hsl(var(--accent))" 
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </Card>
      </DialogContent>
      
      <BidDialog
        open={bidDialogOpen}
        onOpenChange={setBidDialogOpen}
        footballerName={info.name}
        footballerValue={info.value}
        onSubmit={handleBidSubmit}
      />
      
      <ReleaseClauseDialog
        open={releaseClauseDialogOpen}
        onOpenChange={setReleaseClauseDialogOpen}
        footballerName={info.name}
        footballerId={footballerId}
        onSubmit={handleReleaseClauseSubmit}
        onScheduleSubmit={handleScheduleReleaseClauseBidSubmit}
      />

      <IncrementReleaseClauseDialog
        open={incrementReleaseClauseDialogOpen}
        onOpenChange={setIncrementReleaseClauseDialogOpen}
        footballerName={info.name}
        footballerId={footballerId}
        onSubmit={handleIncrementReleaseClause}
      />
    </Dialog>
  );
};