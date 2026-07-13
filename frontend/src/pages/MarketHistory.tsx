import { useEffect, useState, useRef, useCallback } from "react";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { FootballerInfoDialog } from "@/components/FootballerInfoDialog";
import { ArrowRight } from "lucide-react";
import { getActiveLeagueId, fetchMarketHistory, MarketHistoryBid, BACKEND_URL } from "@/lib/api";

const MarketHistory = () => {
  const leagueId = getActiveLeagueId();
  const [bids, setBids] = useState<MarketHistoryBid[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [selectedFootballerId, setSelectedFootballerId] = useState<number | null>(null);
  const observerTarget = useRef<HTMLDivElement>(null);

  const loadBids = useCallback(async (pageNum: number, reset = false) => {
    try {
      if (pageNum === 1) {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }

      const limit = 30;
      const offset = (pageNum - 1) * limit;
      const data = await fetchMarketHistory(limit, offset);

      if (data.bids.length < limit) {
        setHasMore(false);
      }

      setBids(prev => reset ? data.bids : [...prev, ...data.bids]);
    } catch (error) {
      console.error('Error loading market history:', error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    setBids([]);
    setPage(1);
    setHasMore(true);
    loadBids(1, true);
  }, [loadBids]);

  useEffect(() => {
    const observer = new IntersectionObserver(
      entries => {
        if (entries[0].isIntersecting && hasMore && !loading && !loadingMore) {
          setPage(prev => prev + 1);
        }
      },
      { threshold: 0.1 }
    );

    const currentTarget = observerTarget.current;
    if (currentTarget) {
      observer.observe(currentTarget);
    }

    return () => {
      if (currentTarget) {
        observer.unobserve(currentTarget);
      }
    };
  }, [hasMore, loading, loadingMore]);

  useEffect(() => {
    if (page > 1) {
      loadBids(page);
    }
  }, [page, loadBids]);

  const formatAmount = (amount: number) => new Intl.NumberFormat('en-ES', {
    style: 'currency',
    currency: 'EUR',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(amount);

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 pb-20">
      <Header showBackButton />
      <NavigationTabs leagueId={leagueId ?? undefined} />

      <main className="container mx-auto px-2 sm:px-6 lg:px-8 py-4 sm:py-8">
        {loading ? (
          <LoadingSkeleton type="footballers" />
        ) : (
          <div className="space-y-3">
            <div className="rounded-xl border border-border bg-card shadow-lg overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-border/50">
                    <TableHead className="text-muted-foreground font-semibold">Footballer</TableHead>
                    <TableHead className="text-muted-foreground font-semibold">From / To</TableHead>
                    <TableHead className="text-center text-muted-foreground font-semibold">Amount</TableHead>
                    <TableHead className="text-center text-muted-foreground font-semibold hidden sm:table-cell">Timestamp</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {bids.map((bid) => (
                    <TableRow
                      key={`${bid.footballerId}-${bid.timestamp}-${bid.amount}`}
                      className="fade-in cursor-pointer hover:bg-accent/50"
                      onClick={() => setSelectedFootballerId(bid.footballerId)}
                    >
                      <TableCell className="min-w-0">
                        <div className="flex items-center gap-3 min-w-0">
                          <Avatar className="h-12 w-12 border-2 border-secondary/30 flex-shrink-0">
                            <AvatarImage src={`${BACKEND_URL}/footballer/image/${bid.footballerId}`} />
                            <AvatarFallback className="bg-gradient-primary text-white font-semibold text-xs">
                              {getInitials(bid.footballerName)}
                            </AvatarFallback>
                          </Avatar>
                          <span className="font-semibold truncate">{bid.footballerName}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2 min-w-0">
                          <span className="truncate">{bid.fromPlayerName}</span>
                          <ArrowRight className="h-4 w-4 flex-shrink-0 text-muted-foreground" />
                          <span className="truncate">{bid.toPlayerName}</span>
                        </div>
                      </TableCell>
                      <TableCell className="text-center text-secondary font-semibold">
                        {formatAmount(bid.amount)}
                      </TableCell>
                      <TableCell className="text-center hidden sm:table-cell text-muted-foreground">
                        {bid.timestamp}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>

            {loadingMore && (
              <div className="mt-4">
                <LoadingSkeleton type="footballers" />
              </div>
            )}

            <div ref={observerTarget} className="h-4" />

            {!hasMore && bids.length > 0 && (
              <p className="text-center text-muted-foreground mt-4">No more market history to load</p>
            )}
          </div>
        )}
      </main>

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

export default MarketHistory;