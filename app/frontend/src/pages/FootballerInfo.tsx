import { useState, useEffect, useRef, useCallback } from "react";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { SquadRow } from "@/components/SquadRow";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { fetchAllFootballers, AllFootballer } from "@/lib/api";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FootballerInfoDialog } from "@/components/FootballerInfoDialog";

const FootballerInfo = () => {
  const [footballers, setFootballers] = useState<AllFootballer[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [page, setPage] = useState(1);
  const [hasMore, setHasMore] = useState(true);
  const [sortBy, setSortBy] = useState<'name' | 'points' | 'value'>('name');
  const [selectedFootballerId, setSelectedFootballerId] = useState<number | null>(null);
  const observerTarget = useRef<HTMLDivElement>(null);

  const loadFootballers = useCallback(async (pageNum: number, sort: 'name' | 'points' | 'value', reset = false) => {
    try {
      if (pageNum === 1) {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }

      const data = await fetchAllFootballers(pageNum, 50, sort);
      
      if (data.length < 50) {
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
    loadFootballers(1, sortBy, true);
  }, [sortBy, loadFootballers]);

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
      loadFootballers(page, sortBy);
    }
  }, [page, sortBy, loadFootballers]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-primary/5">
      <Header />
      <NavigationTabs />
      
      <div className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="flex justify-between items-center mb-6">
          <h1 className="text-3xl font-bold text-foreground">All Footballers</h1>
          <Select value={sortBy} onValueChange={(value: 'name' | 'points' | 'value') => setSortBy(value)}>
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Sort by" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="name">Sort by Name</SelectItem>
              <SelectItem value="points">Sort by Points</SelectItem>
              <SelectItem value="value">Sort by Value</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {loading ? (
          <LoadingSkeleton type="footballers" />
        ) : (
          <>
            <div className="rounded-xl border border-border bg-card shadow-lg overflow-hidden">
              <Table>
                <TableHeader>
                  <TableRow className="hover:bg-transparent border-border/50">
                    <TableHead className="text-muted-foreground font-semibold">Player</TableHead>
                    <TableHead className="text-center text-muted-foreground font-semibold">Value</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {footballers.map((footballer) => (
                    <SquadRow
                      key={footballer.id}
                      id={footballer.id}
                      name={footballer.name}
                      value={footballer.value}
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
    </div>
  );
};

export default FootballerInfo;
