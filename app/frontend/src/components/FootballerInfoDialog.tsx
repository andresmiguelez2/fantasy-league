import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Card } from "@/components/ui/card";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { fetchFootballerInfo, fetchFixtureDetail, FootballerInfo, FixtureDetail } from "@/lib/api";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Brush, Cell } from "recharts";

interface FootballerInfoDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  footballerId: number;
  footballerName?: string;
}

export const FootballerInfoDialog = ({
  open,
  onOpenChange,
  footballerId,
  footballerName,
}: FootballerInfoDialogProps) => {
  const [info, setInfo] = useState<FootballerInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [imgError, setImgError] = useState(false);
  const [selectedFixture, setSelectedFixture] = useState<number | null>(null);
  const [fixtureDetail, setFixtureDetail] = useState<FixtureDetail | null>(null);

  useEffect(() => {
    if (open) {
      setLoading(true);
      setSelectedFixture(null);
      setFixtureDetail(null);
      fetchFootballerInfo(footballerId)
        .then(setInfo)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [open, footballerId]);

  // Set default fixture to latest when info loads
  useEffect(() => {
    if (info && info.fixture_breakdown.length > 0) {
      const latestFixture = Math.max(...info.fixture_breakdown.map(f => f.fixture));
      setSelectedFixture(latestFixture);
    }
  }, [info]);

  // Fetch fixture detail when selected fixture changes
  useEffect(() => {
    if (selectedFixture !== null && footballerId) {
      fetchFixtureDetail(footballerId, selectedFixture)
        .then(setFixtureDetail)
        .catch(console.error);
    }
  }, [selectedFixture, footballerId]);

  const formatValue = (val: number) => {
    return new Intl.NumberFormat('en-ES', {
      style: 'currency',
      currency: 'EUR',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(val);
  };

  const getInitials = (name: string) => {
    return name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2);
  };

  const handleBarClick = (data: any) => {
    if (data && data.activePayload && data.activePayload[0]) {
      setSelectedFixture(data.activePayload[0].payload.fixture);
    }
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
                  src={`${import.meta.env.VITE_BACKEND_URL}/footballer/image/${footballerId}`}
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
              <h3 className="text-2xl font-bold text-center">{info.name}</h3>
              <p className="text-sm text-muted-foreground text-center">{info.team}</p>
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

            <Card className="p-4">
              <p className="text-sm text-muted-foreground">Market Value</p>
              <p className="text-2xl font-bold text-accent">{formatValue(info.market_value)}</p>
            </Card>
          </div>
        </div>

        {/* Fixture Breakdown Bar Chart */}
        <Card className="p-6 mb-6">
          <h3 className="text-lg font-semibold mb-4">Points by Fixture {selectedFixture && <span className="text-muted-foreground text-sm">(Selected: {selectedFixture})</span>}</h3>
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
    </Dialog>
  );
};