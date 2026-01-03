import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { FootballerCard } from "@/components/FootballerCard";
import { BidDialog } from "@/components/BidDialog";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { PlayerInfoRibbon } from "@/components/PlayerInfoRibbon";
import { FootballerInfoDialog } from "@/components/FootballerInfoDialog";
import { fetchMarketFootballers, placeBid, MarketFootballer } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useParams } from "react-router-dom";
import { useAuth } from "@/contexts/AuthContext";

// Sample placeholder data for visualization
const sampleFootballers: MarketFootballer[] = [
  { id: 151, name: "Sofyan Amrabat", value: 7433594, ownerId: "Alice", onMarketSince: "2025-11-02T11:29:59+00:00", bidAmount: 8000000, averagePoints: 3.67, totalPoints: 22 },
  { id: 134, name: "Pablo Fornals", value: 71021079, ownerId: "Charlotte", onMarketSince: "2025-11-08T10:00:00+00:00", bidAmount: 75000000, averagePoints: 7.27, totalPoints: 80 },
  { id: 241, name: "Carlos Álvarez", value: 10314687, ownerId: "Daniel", onMarketSince: "2025-11-08T10:45:00+00:00", bidAmount: 0, averagePoints: 4.64, totalPoints: 51 },
  { id: 270, name: "Samú Costa", value: 2140263, ownerId: "Bob", onMarketSince: "2025-11-08T21:59:55+00:00", bidAmount: 2500000, averagePoints: 4.0, totalPoints: 36 },
  { id: 185, name: "Javi Puado", value: 14581650, ownerId: "Emma", onMarketSince: "2025-11-08T21:59:55+00:00", bidAmount: 0, averagePoints: 5.13, totalPoints: 41 },
  { id: 177, name: "Joseph Aidoo", value: 655543, ownerId: "Frank", onMarketSince: "2025-11-08T21:59:55+00:00", bidAmount: 0, averagePoints: "", totalPoints: 0 },
  { id: 158, name: "Coke Carrillo", value: 1567556, ownerId: "Grace", onMarketSince: "2025-11-08T21:59:55+00:00", bidAmount: 0, averagePoints: "", totalPoints: 0 },
  { id: 133, name: "Cédric Bakambu", value: 920371, ownerId: "Henry", onMarketSince: "2025-11-08T21:59:55+00:00", bidAmount: 950000, averagePoints: 1.88, totalPoints: 15 },
];

const Market = () => {
  const { playerId } = useParams();
  const { user } = useAuth();
  const [footballers, setFootballers] = useState<MarketFootballer[]>([]);
  const [loading, setLoading] = useState(true);
  const [bidDialogOpen, setBidDialogOpen] = useState(false);
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  const [selectedFootballer, setSelectedFootballer] = useState<MarketFootballer | null>(null);
  const { toast } = useToast();
  
  useEffect(() => {
    const loadFootballers = async () => {
      setLoading(true);
      try {
        // Use playerId from URL params or default to logged-in user
        const id = playerId || user?.playerId?.toString() || localStorage.getItem("playerId") || "1";
        const data = await fetchMarketFootballers(id);
        setFootballers(data);
      } catch (error) {
        console.log('Failed to fetch market data, using sample data for visualization');
        // Use sample data when API is not available
        setFootballers(sampleFootballers);
      } finally {
        setLoading(false);
      }
    };
    
    loadFootballers();
  }, [playerId, user?.playerId]);
  
  const handleBidClick = (footballer: MarketFootballer) => {
    setSelectedFootballer(footballer);
    setBidDialogOpen(true);
  };

  const handleFootballerClick = (footballer: MarketFootballer) => {
    setSelectedFootballer(footballer);
    setInfoDialogOpen(true);
  };
  
  const handleBidSubmit = async (amount: number) => {
    if (!selectedFootballer) return;
    
    const id = playerId || user?.playerId?.toString() || localStorage.getItem("playerId") || "1";
    const resp = await placeBid(selectedFootballer.id, id, amount);

    // Determine message from API response
    let message = '';
    if (resp) {
      if (typeof resp === 'string') message = resp;
      else if (resp.message) message = resp.message;
      else if (resp.detail) message = resp.detail;
      else if (resp.text) message = resp.text;
      else message = JSON.stringify(resp);
    }

    toast({
      // title: amount === 0 ? "Bid deleted" : "Bid response",
      description: message || (amount === 0
        ? `Your bid for ${selectedFootballer.name} has been deleted.`
        : `Your bid of €${amount.toLocaleString()} for ${selectedFootballer.name} has been placed.`),
    });
    
    // Update the footballer's value with the new bid
    setFootballers(prev =>
      prev.map(f =>
        f.id === selectedFootballer.id
          ? { ...f, value: amount, bidAmount: amount }
          : f
      )
    );
  };
  
  return (
    <div className="min-h-screen bg-background pb-20">
      <Header showBackButton />
      <NavigationTabs />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {loading ? (
          <LoadingSkeleton type="footballers" />
        ) : (
          <div className="space-y-3 max-w-2xl">
            {footballers.map((footballer) => (
              <FootballerCard
                key={footballer.id}
                id={footballer.id}
                name={footballer.name}
                owner={footballer.ownerId}
                currentBid={footballer.bidAmount}
                totalPoints={footballer.totalPoints}
                averagePoints={footballer.averagePoints}
                showBidButton
                onBid={() => handleBidClick(footballer)}
                onOwnerClick={() => handleFootballerClick(footballer)}
              />
            ))}
          </div>
        )}
      </main>
      
      {selectedFootballer && (
        <>
          <BidDialog
            open={bidDialogOpen}
            onOpenChange={setBidDialogOpen}
            footballerName={selectedFootballer.name}
            currentBid={selectedFootballer.value}
            onSubmit={handleBidSubmit}
          />
          <FootballerInfoDialog
            open={infoDialogOpen}
            onOpenChange={setInfoDialogOpen}
            footballerId={selectedFootballer.id}
            footballerName={selectedFootballer.name}
          />
        </>
      )}
      <PlayerInfoRibbon />
    </div>
  );
};

export default Market;
