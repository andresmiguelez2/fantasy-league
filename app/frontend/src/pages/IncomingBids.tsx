import { useState } from "react";
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { PlayerInfoRibbon } from "@/components/PlayerInfoRibbon";
import { BidReplyDialog } from "@/components/BidReplyDialog";
import { FootballerInfoDialog } from "@/components/FootballerInfoDialog";
import { fetchIncomingBids, replyToBid, IncomingBid } from "@/lib/api";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { MessageSquareReply } from "lucide-react";
import { format } from "date-fns";
import { toast } from "sonner";
import { useAuth } from "@/contexts/AuthContext";

const IncomingBids = () => {
  const [selectedBid, setSelectedBid] = useState<IncomingBid | null>(null);
  const [replyDialogOpen, setReplyDialogOpen] = useState(false);
  const [selectedFootballerId, setSelectedFootballerId] = useState<number | null>(null);
  const queryClient = useQueryClient();
  const { user } = useAuth();
  const playerId = user?.playerId?.toString() || localStorage.getItem("playerId") || "1";

  const { data: bids = [], isLoading } = useQuery({
    queryKey: ["incomingBids", playerId],
    queryFn: () => fetchIncomingBids(playerId),
  });

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return format(date, "dd-MM-yyyy HH:mm");
  };

  const formatCurrency = (value: number) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
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

  const handleBidReply = async (accept: boolean) => {
    if (!selectedBid) return;
    
    try {
      await replyToBid(selectedBid.bidId, accept);
      toast.success(accept ? "Bid accepted" : "Bid declined");
      queryClient.invalidateQueries({ queryKey: ["incomingBids"] });
      setReplyDialogOpen(false);
    } catch (error) {
      toast.error("Failed to reply to bid");
    }
  };

  return (
    <div className="min-h-screen bg-background pb-20">
      <Header />
      <NavigationTabs />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {isLoading ? (
          <p className="text-muted-foreground">Loading bids...</p>
        ) : bids.length === 0 ? (
          <p className="text-muted-foreground">No incoming bids</p>
        ) : (
          <div className="max-w-4xl">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Footballer</TableHead>
                  <TableHead className="text-center">Bidder</TableHead>
                  <TableHead className="text-center">Timestamp</TableHead>
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
                          src={`${import.meta.env.VITE_BACKEND_URL}/footballer/image/${bid.footballerId}`}
                          alt={bid.footballerName}
                          className="w-10 h-10 rounded-full object-cover"
                        />
                        <span className="font-medium">{bid.footballerName}</span>
                      </div>
                    </TableCell>
                    <TableCell className="text-center text-muted-foreground">
                      {bid.bidderId}
                    </TableCell>
                    <TableCell className="text-center text-muted-foreground">
                      {formatTimestamp(bid.timestamp)}
                    </TableCell>
                    <TableCell className="text-center font-semibold">
                      {formatCurrency(bid.amount)}
                    </TableCell>
                    <TableCell>
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={(e) => handleReplyClick(e, bid)}
                      >
                        <MessageSquareReply className="h-4 w-4" />
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
          bidAmount={selectedBid.amount}
          onAccept={() => handleBidReply(true)}
          onDecline={() => handleBidReply(false)}
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
