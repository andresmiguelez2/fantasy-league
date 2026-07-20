import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { PlayerInfoRibbon } from "@/components/PlayerInfoRibbon";
import { FootballerInfoDialog } from "@/components/FootballerInfoDialog";
import { fetchIncomingBids, BACKEND_URL } from "@/lib/api";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { format } from "date-fns";
import { getActiveLeagueId, getActivePlayerId } from "@/lib/api";

const IncomingBids = () => {
  const [selectedFootballerId, setSelectedFootballerId] = useState<number | null>(null);
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

  const handleRowClick = (footballerId: number) => {
    setSelectedFootballerId(footballerId);
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
                  <TableHead className="text-center hidden sm:table-cell">Bidder</TableHead>
                  <TableHead className="text-center hidden sm:table-cell">Timestamp</TableHead>
                  <TableHead className="text-center">Bid Value</TableHead>
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
                      {bid.bidderName}
                    </TableCell>
                    <TableCell className="text-center text-muted-foreground hidden sm:table-cell">
                      {formatTimestamp(bid.timestamp)}
                    </TableCell>
                    <TableCell className="text-center font-semibold">
                      {formatCurrency(bid.amount)}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </main>

      <PlayerInfoRibbon />

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
