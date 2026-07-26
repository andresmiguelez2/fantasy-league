import { useState, useEffect, useRef, useCallback } from "react";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FootballerInfoRow } from "@/components/FootballerInfoRow";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { fetchAllFootballers, MarketFootballer } from "@/lib/api";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FootballerInfoDialog } from "@/components/FootballerInfoDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ArrowUpDown } from "lucide-react";
import { getActiveLeagueId } from "@/lib/api";
import { PlayerInfoRibbon } from "@/components/PlayerInfoRibbon";

const FootballerInfo = () => {
  const leagueId = getActiveLeagueId();
  const [footballers, setFootballers] = useState<MarketFootballer[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [sortBy, setSortBy] = useState<'name' | 'points' | 'value'>('name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');
  const [search, setSearch] = useState('');
  const [selectedFootballerId, setSelectedFootballerId] = useState<number | null>(null);
  const observerTarget = useRef<HTMLDivElement>(null);

  const loadFootballers = useCallback(async (
    pageNum: number, 
    sort: 'name' | 'points' | 'value', 
    order: 'asc' | 'desc',
    searchTerm: string,
    reset = false
  ) => {
    try {
      if (pageNum === 1) {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }

      const data = await fetchAllFootballers(pageNum, 30, sort, order, searchTerm);
      
      if (data.length < 30) {
        setHasMore(false);
      }

      setFootballers(prev => reset ? data : [...prev, ...data]);
    } catch (error) {
      console.error('Error loading footballers:', error);
    } finally {
      setLoading(false);
      setLoadingMore(false);
    }
  }, []);

  useEffect(() => {
    setFootballers([]);
    setPage(1);
    setHasMore(true);
    loadFootballers(1, sortBy, sortOrder, search, true);
  }, [sortBy, sortOrder, search, loadFootballers]);

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
      loadFootballers(page, sortBy, sortOrder, search);
    }
  }, [page, sortBy, sortOrder, search, loadFootballers]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5 pb-20">
      <Header />
      <NavigationTabs leagueId={leagueId} />
      
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex flex-col gap-4 mb-6">
          <h1 className="text-3xl font-bold text-foreground">All Footballers</h1>
          <div className="flex gap-2 items-center flex-wrap">
            <Input
              placeholder="Search footballers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-xs"
            />
            <Select value={sortBy} onValueChange={(value: 'name' | 'points' | 'value') => setSortBy(value)}>
              <SelectTrigger className="w-[180px]">
                <SelectValue placeholder="Sort by" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="name">Name</SelectItem>
                <SelectItem value="points">Points</SelectItem>
                <SelectItem value="value">Value</SelectItem>
              </SelectContent>
            </Select>
            <Button
              variant="outline"
              size="icon"
              onClick={() => setSortOrder(prev => prev === 'asc' ? 'desc' : 'asc')}
            >
              <ArrowUpDown className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {loading ? (
          <LoadingSkeleton type="footballers" />
        ) : (
          <>
            <div className="rounded-xl border border-border bg-card shadow-lg overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-border/50">
                    <TableHead className="text-muted-foreground font-semibold">Player</TableHead>
                    <TableHead className="text-center text-muted-foreground font-semibold">Pos</TableHead>
                    <TableHead className="text-center text-muted-foreground font-semibold">Avail</TableHead>
                    <TableHead className="text-center text-muted-foreground font-semibold">Total Points</TableHead>
                    <TableHead className="text-center text-muted-foreground font-semibold hidden sm:table-cell">Average Points</TableHead>
                    <TableHead className="text-center text-muted-foreground font-semibold hidden sm:table-cell">Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {footballers.map((footballer) => (
                    <FootballerInfoRow
                      key={footballer.id}
                      id={footballer.id}
                      name={footballer.name}
                      value={footballer.value}
                      ownerId={footballer.ownerId}
                      averagePoints={footballer.averagePoints}
                      totalPoints={footballer.totalPoints}
                      position={footballer.position}
                      availability={footballer.availability}
                      onClick={() => setSelectedFootballerId(footballer.id)}
                    />
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

            {!hasMore && footballers.length > 0 && (
              <p className="text-center text-muted-foreground mt-4">No more footballers to load</p>
            )}
          </>
        )}
      </div>

      {selectedFootballerId && (
        <FootballerInfoDialog
          footballerId={selectedFootballerId}
          open={!!selectedFootballerId}
          onOpenChange={(open) => !open && setSelectedFootballerId(null)}
        />
      )}

      <PlayerInfoRibbon />
    </div>
  );
};

export default FootballerInfo;
