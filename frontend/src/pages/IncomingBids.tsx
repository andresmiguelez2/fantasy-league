import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { PlayerInfoRibbon } from "@/components/PlayerInfoRibbon";
import { BidReplyDialog } from "@/components/BidReplyDialog";
import { FootballerInfoDialog } from "@/components/FootballerInfoDialog";
import { fetchIncomingBids, replyToBid, IncomingBid, BACKEND_URL } from "@/lib/api";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { MessageCircle } from "lucide-react";
import { format } from "date-fns";
import { toast } from "sonner";
import { getActiveLeagueId, getActivePlayerId } from "@/lib/api";

const IncomingBids = () => {
  const [selectedBid, setSelectedBid] = useState<IncomingBid | null>(null);
  const [replyDialogOpen, setReplyDialogOpen] = useState(false);
  const [selectedFootballerId, setSelectedFootballerId] = useState<number | null>(null);
  const queryClient = useQueryClient();
  const playerId = getActivePlayerId();
  const leagueId = getActiveLeagueId();

  const { data: bids = [], isLoading } = useQuery({
    queryKey: ["incomingBids", playerId],
    queryFn: () => {
      if (!playerId) {
        return Promise.resolve([]);
      }
      return fetchIncomingBids(playerId);
    },
  });

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return format(date, "dd/MM/yy HH:mm");
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
      notation: 'compact',
      maximumFractionDigits: 1,
    }).format(value);
  };

  const handleReplyClick = (e: React.MouseEvent, bid: IncomingBid) => {
    e.stopPropagation();
    setSelectedBid(bid);
    setReplyDialogOpen(true);
  };

  const handleRowClick = (footballerId: number) => {
    setSelectedFootballerId(footballerId);
  };

  const handleAccept = async () => {
    if (!selectedBid || !leagueId) return;
    try {
      const success = await replyToBid(selectedBid.bidId, true, leagueId);
      if (success) {
        toast.success("Bid accepted");
        queryClient.invalidateQueries({ queryKey: ["incomingBids"] });
        setReplyDialogOpen(false);
      } else {
        toast.error("Failed to accept bid");
      }
    } catch {
      toast.error("Failed to accept bid");
    }
  };

  const handleDecline = async () => {
    if (!selectedBid || !leagueId) return;
    try {
      const success = await replyToBid(selectedBid.bidId, false, leagueId);
      if (success) {
        toast.success("Bid declined");
        queryClient.invalidateQueries({ queryKey: ["incomingBids"] });
        setReplyDialogOpen(false);
      } else {
        toast.error("Failed to decline bid");
      }
    } catch {
      toast.error("Failed to decline bid");
    }
  };

  return (
    <div className="min-h-screen bg-background pb-20">
      <Header />
      <NavigationTabs leagueId={leagueId} />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <p className="text-muted-foreground">Loading bids...</p>
        ) : bids.length === 0 ? (
          <p className="text-muted-foreground">No past incoming bids</p>
        ) : (
          <div className="max-w-4xl overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Footballer</TableHead>
                  <TableHead className="text-center">Bidder</TableHead>
                  <TableHead className="text-center">Timestamp</TableHead>
                  <TableHead className="text-center">Value</TableHead>
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
                    <TableCell className="whitespace-normal break-words">
                      <div className="flex items-center gap-3">
                        <img
                          src={`${BACKEND_URL}/footballer/image/${bid.footballerId}`}
                          alt={bid.footballerName}
                          className="w-8 h-8 sm:w-10 sm:h-10 rounded-full object-cover flex-shrink-0"
                        />
                        <span className="font-medium break-words">{bid.footballerName}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center text-muted-foreground whitespace-normal break-words">
                      {bid.bidderName}
                    </TableCell>
                    <TableCell className="text-center text-muted-foreground whitespace-normal break-words">
                      {formatTimestamp(bid.timestamp)}
                    </TableCell>
                    <TableCell className="text-center font-semibold whitespace-normal break-words">
                      {formatCurrency(bid.amount)}
                    </TableCell>
                    <TableCell>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => handleReplyClick(e, bid)}
                      >
                        <MessageCircle className="h-4 w-4" />
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
        <BidReplyDialog
          open={replyDialogOpen}
          onOpenChange={setReplyDialogOpen}
          footballerName={selectedBid.footballerName}
          bidderName={selectedBid.bidderName}
          bidAmount={selectedBid.amount}
          onAccept={handleAccept}
          onDecline={handleDecline}
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

export default IncomingBids;