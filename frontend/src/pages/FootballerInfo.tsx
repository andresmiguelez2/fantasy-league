import { useState, useEffect, useRef, useCallback } from "react";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { FootballerInfoRow } from "@/components/FootballerInfoRow";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { fetchAllFootballers, FootballerFilterOptions, FootballerFilters, MarketFootballer } from "@/lib/api";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { FootballerInfoDialog } from "@/components/FootballerInfoDialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ArrowUpDown } from "lucide-react";
import { getActiveLeagueId } from "@/lib/api";
import { PlayerInfoRibbon } from "@/components/PlayerInfoRibbon";

const DEFAULT_FILTERS: FootballerFilters = {
  teams: [],
  positions: [],
  availabilities: [],
};

const DEFAULT_FILTER_OPTIONS: FootballerFilterOptions = {
  teams: [],
  positions: [],
  availabilities: [],
};

const POSITION_LABELS: Record<string, string> = {
  gk: "GK",
  df: "DF",
  md: "MD",
  fw: "FW",
};

const formatAvailability = (value: string) =>
  value
    .split(" ")
    .map((part) => part.charAt(0).toUpperCase() + part.slice(1).toLowerCase())
    .join(" ");

interface FilterDropdownProps {
  label: string;
  options: string[];
  selected: string[];
  onToggle: (value: string) => void;
  formatOption?: (value: string) => string;
}

const FilterDropdown = ({ label, options, selected, onToggle, formatOption = (value) => value }: FilterDropdownProps) => (
  <DropdownMenu>
    <DropdownMenuTrigger asChild>
      <Button variant="outline" className="min-w-[180px] justify-between">
        <span className="truncate">
          {selected.length > 0 ? `${label} (${selected.length})` : label}
        </span>
      </Button>
    </DropdownMenuTrigger>
    <DropdownMenuContent align="start" className="w-56">
      {options.map((option) => (
        <DropdownMenuCheckboxItem
          key={option}
          checked={selected.includes(option)}
          onCheckedChange={() => onToggle(option)}
          onSelect={(event) => event.preventDefault()}
        >
          {formatOption(option)}
        </DropdownMenuCheckboxItem>
      ))}
    </DropdownMenuContent>
  </DropdownMenu>
);

const FootballerInfo = () => {
  const leagueId = getActiveLeagueId();
  const [footballers, setFootballers] = useState<MarketFootballer[]>([]);
  const [filterOptions, setFilterOptions] = useState<FootballerFilterOptions>(DEFAULT_FILTER_OPTIONS);
  const [filters, setFilters] = useState<FootballerFilters>(DEFAULT_FILTERS);
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
    selectedFilters: FootballerFilters,
    reset = false
  ) => {
    try {
      if (pageNum === 1) {
        setLoading(true);
      } else {
        setLoadingMore(true);
      }

      const data = await fetchAllFootballers(pageNum, 30, sort, order, searchTerm, selectedFilters);
      
      if (data.footballers.length < 30) {
        setHasMore(false);
      }

      setFilterOptions(data.filterOptions);
      setFootballers(prev => reset ? data.footballers : [...prev, ...data.footballers]);
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
    loadFootballers(1, sortBy, sortOrder, search, filters, true);
  }, [sortBy, sortOrder, search, filters, loadFootballers]);

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
      loadFootballers(page, sortBy, sortOrder, search, filters);
    }
  }, [page, sortBy, sortOrder, search, filters, loadFootballers]);

  const toggleFilter = (key: keyof FootballerFilters, value: string) => {
    setFilters((prev) => {
      const nextValues = prev[key].includes(value)
        ? prev[key].filter((entry) => entry !== value)
        : [...prev[key], value];

      return {
        ...prev,
        [key]: nextValues,
      };
    });
  };

  return (
    <div className="min-h-screen bg-background pb-20">
      <Header />
      <NavigationTabs leagueId={leagueId} />
      
      <main className="container mx-auto px-2 sm:px-6 lg:px-8 py-4 sm:py-8">
        <div className="flex flex-col gap-4 mb-6">
          <h1 className="text-3xl font-bold text-foreground">All Footballers</h1>
          <div className="flex gap-2 items-center flex-wrap">
            <Input
              placeholder="Search footballers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-xs"
            />
            <FilterDropdown
              label="Team"
              options={filterOptions.teams}
              selected={filters.teams}
              onToggle={(value) => toggleFilter("teams", value)}
            />
            <FilterDropdown
              label="Position"
              options={filterOptions.positions}
              selected={filters.positions}
              onToggle={(value) => toggleFilter("positions", value)}
              formatOption={(value) => POSITION_LABELS[value.toLowerCase()] ?? value.toUpperCase()}
            />
            <FilterDropdown
              label="Availability"
              options={filterOptions.availabilities}
              selected={filters.availabilities}
              onToggle={(value) => toggleFilter("availabilities", value)}
              formatOption={formatAvailability}
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
            <div className="max-w-4xl overflow-x-auto">
              <Table className="table-fixed w-full">
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[40%]">Name</TableHead>
                    <TableHead className="w-[10%] text-center"></TableHead>
                    <TableHead className="w-[10%] text-center"></TableHead>
                    <TableHead className="w-[18%] text-center">Points</TableHead>
                    <TableHead className="w-[22%] text-center">Value</TableHead>
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
      </main>

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
