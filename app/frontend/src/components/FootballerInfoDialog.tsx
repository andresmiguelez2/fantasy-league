import { useEffect, useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { fetchFootballerInfo, FootballerInfo } from "@/lib/api";
import { BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { X } from "lucide-react";

interface FootballerInfoDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  footballerId: number;
  footballerName: string;
}

export const FootballerInfoDialog = ({
  open,
  onOpenChange,
  footballerId,
  footballerName,
}: FootballerInfoDialogProps) => {
  const [info, setInfo] = useState<FootballerInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (open) {
      setLoading(true);
      fetchFootballerInfo(footballerId)
        .then(setInfo)
        .catch(console.error)
        .finally(() => setLoading(false));
    }
  }, [open, footballerId]);

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

  // Sort fixture breakdown by fixture number ascending
  const sortedFixtures = [...info.fixture_breakdown].sort((a, b) => a.fixture - b.fixture);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="sr-only">Footballer Information</DialogTitle>
        </DialogHeader>

        {/* Top Section */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          {/* Left: Footballer Image */}
          <Card className="p-6 flex items-center justify-center">
            <Avatar className="h-48 w-48 border-4 border-secondary/30">
              <AvatarImage src={`${import.meta.env.VITE_BACKEND_URL}/images/${footballerId}`} />
              <AvatarFallback className="bg-gradient-primary text-white font-semibold text-4xl">
                {getInitials(info.name)}
              </AvatarFallback>
            </Avatar>
          </Card>

          {/* Right: Info Boxes */}
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
          <h3 className="text-lg font-semibold mb-4">Points by Fixture</h3>
          <ResponsiveContainer width="100%" height={250}>
            <BarChart data={sortedFixtures}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis 
                dataKey="fixture" 
                label={{ value: 'Fixture', position: 'insideBottom', offset: -5 }}
              />
              <YAxis 
                label={{ value: 'Points', angle: -90, position: 'insideLeft' }}
              />
              <Tooltip />
              <Bar dataKey="points" fill="hsl(var(--primary))" />
            </BarChart>
          </ResponsiveContainer>
        </Card>

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
                tickFormatter={(value) => `€${(value / 1000).toFixed(0)}k`}
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

        {/* Bottom Close Button */}
        <div className="flex justify-center pt-4 border-t">
          <Button 
            onClick={() => onOpenChange(false)} 
            variant="outline"
            className="gap-2"
          >
            <X className="h-4 w-4" />
            Close
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};
