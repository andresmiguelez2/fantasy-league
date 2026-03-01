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
        const id = playerId || user?.playerId?.toString();
        const data = await fetchMarketFootballers(id);
        setFootballers(data);
      } catch (error) {
        console.error('Failed to fetch market data:', error);
        setFootballers([]);
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
    
    const id = playerId || user?.playerId?.toString();
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
      
      <main className="container mx-auto px-2 sm:px-6 lg:px-8 py-4 sm:py-8">
        {loading ? (
          <LoadingSkeleton type="footballers" />
        ) : (
          <div className="space-y-2 sm:space-y-3 max-w-2xl">
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
            ownerId={selectedFootballer.ownerId}
            onBid={() => handleBidClick(selectedFootballer)}
          />
        </>
      )}
      <PlayerInfoRibbon />
    </div>
  );
};

export default Market;
