import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { PlayerInfoRibbon } from "@/components/PlayerInfoRibbon";
import { BidDialog } from "@/components/BidDialog";
import { FootballerInfoDialog } from "@/components/FootballerInfoDialog";
import { fetchFutureBids, submitBid, OutgoingBid, BACKEND_URL } from "@/lib/api";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Edit } from "lucide-react";
import { format } from "date-fns";
import { toast } from "sonner";
import { getActiveLeagueId, getActivePlayerId } from "@/lib/api";

const FutureBids = () => {
  const [selectedBid, setSelectedBid] = useState<OutgoingBid | null>(null);
  const [bidDialogOpen, setBidDialogOpen] = useState(false);
  const [selectedFootballerId, setSelectedFootballerId] = useState<number | null>(null);
  const queryClient = useQueryClient();
  const playerId = getActivePlayerId();
  const leagueId = getActiveLeagueId();

  const { data: bids = [], isLoading } = useQuery({
    queryKey: ["futureBids", playerId],
    queryFn: () => {
      if (!playerId) {
        return Promise.resolve([]);
      }
      return fetchFutureBids(playerId);
    },
  });

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return format(date, "dd-MM-yyyy HH:mm");
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat("en-US", {
      style: "currency",
      currency: "EUR",
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  const handleEditClick = (e: React.MouseEvent, bid: OutgoingBid) => {
    e.stopPropagation();
    setSelectedBid(bid);
    setBidDialogOpen(true);
  };

  const handleRowClick = (footballerId: number) => {
    setSelectedFootballerId(footballerId);
  };

  const handleBidSubmit = async (amount: number, timestamp?: string | null) => {
    if (!selectedBid) return false;
    if (!playerId) {
      toast.error("No active player selected");
      return false;
    }

    try {
      const submitted = await submitBid(
        selectedBid.footballerId,
        playerId,
        amount,
        timestamp,
        selectedBid.bidId,
      );
      if (!submitted) {
        toast.error("Failed to update bid");
        return false;
      }

      toast.success(amount === 0 ? "Bid deleted" : "Bid updated");
      queryClient.invalidateQueries({ queryKey: ["futureBids"] });
      queryClient.invalidateQueries({ queryKey: ["outgoingBids"] });
      return true;
    } catch (error) {
      toast.error("Failed to update bid");
      return false;
    }
  };

  return (
    <div className="min-h-screen bg-background pb-20">
      <Header />
      <NavigationTabs leagueId={leagueId} />

      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <p className="mb-4 text-sm text-muted-foreground">
          Scheduled bids stay here until their timestamp becomes active.
        </p>
        {isLoading ? (
          <p className="text-muted-foreground">Loading bids...</p>
        ) : bids.length === 0 ? (
          <p className="text-muted-foreground">No future bids</p>
        ) : (
          <div className="max-w-4xl overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Footballer</TableHead>
                  <TableHead className="text-center hidden sm:table-cell">Owner</TableHead>
                  <TableHead className="text-center hidden sm:table-cell">Scheduled For</TableHead>
                  <TableHead className="text-center">Bid Value</TableHead>
                  <TableHead className="w-[80px]"></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {bids.map((bid) => (
                  <TableRow
                    key={bid.bidId}
                    className="cursor-pointer"
                    onClick={() => handleRowClick(bid.footballerId)}
                  >
                    <TableCell>
                      <div className="flex items-center gap-3">
                        <img
                          src={`${BACKEND_URL}/footballer/image/${bid.footballerId}`}
                          alt={bid.footballerName}
                          className="w-8 h-8 sm:w-10 sm:h-10 rounded-full object-cover flex-shrink-0"
                        />
                        <span className="font-medium truncate">{bid.footballerName}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center text-muted-foreground hidden sm:table-cell">
                      {bid.ownerName ?? "-"}
                    </TableCell>
                    <TableCell className="text-center text-muted-foreground hidden sm:table-cell">
                      {formatTimestamp(bid.timestamp)}
                    </TableCell>
                    <TableCell className="text-center font-semibold">
                      {formatCurrency(bid.amount)}
                    </TableCell>
                    <TableCell>
                      <Button size="sm" variant="outline" onClick={(e) => handleEditClick(e, bid)}>
                        <Edit className="h-4 w-4" />
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </main>

      <PlayerInfoRibbon />

      {selectedBid && (
        <BidDialog
          open={bidDialogOpen}
          onOpenChange={setBidDialogOpen}
          footballerName={selectedBid.footballerName}
          currentBid={selectedBid.amount}
          currentBidTimestamp={selectedBid.timestamp}
          onSubmit={handleBidSubmit}
        />
      )}

      {selectedFootballerId && (
        <FootballerInfoDialog
          footballerId={selectedFootballerId}
          open={!!selectedFootballerId}
          onOpenChange={(open) => !open && setSelectedFootballerId(null)}
        />
      )}
    </div>
  );
};

export default FutureBids;
