import { useEffect, useState } from "react";
import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { FootballerCard } from "@/components/FootballerCard";
import { BidDialog } from "@/components/BidDialog";
import { LoadingSkeleton } from "@/components/LoadingSkeleton";
import { fetchMarketFootballers, placeBid, MarketFootballer } from "@/lib/api";
import { useToast } from "@/hooks/use-toast";
import { useParams } from "react-router-dom";

const Market = () => {
  const { playerId } = useParams();
  const [footballers, setFootballers] = useState<MarketFootballer[]>([]);
  const [loading, setLoading] = useState(true);
  const [bidDialogOpen, setBidDialogOpen] = useState(false);
  const [selectedFootballer, setSelectedFootballer] = useState<MarketFootballer | null>(null);
  const { toast } = useToast();
  
  useEffect(() => {
    const loadFootballers = async () => {
      setLoading(true);
      // Use playerId from URL params or default to '1' for current user
      const id = playerId || '1';
      const data = await fetchMarketFootballers(id);
      setFootballers(data);
      setLoading(false);
    };
    
    loadFootballers();
  }, []);
  
  const handleBidClick = (footballer: MarketFootballer) => {
    setSelectedFootballer(footballer);
    setBidDialogOpen(true);
  };
  
  const handleBidSubmit = async (amount: number) => {
    if (!selectedFootballer) return;
    
    await placeBid(selectedFootballer.id, amount);
    
    toast({
      title: "Bid placed successfully",
      description: `Your bid of €${amount.toLocaleString()} for ${selectedFootballer.name} has been placed.`,
    });
    
    // Update the footballer's value with the new bid
    setFootballers(prev =>
      prev.map(f =>
        f.id === selectedFootballer.id
          ? { ...f, value: amount }
          : f
      )
    );
  };
  
  return (
    <div className="min-h-screen bg-background">
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
                name={footballer.name}
                currentBid={footballer.value}
                showBidButton
                onBid={() => handleBidClick(footballer)}
              />
            ))}
          </div>
        )}
      </main>
      
      {selectedFootballer && (
        <BidDialog
          open={bidDialogOpen}
          onOpenChange={setBidDialogOpen}
          footballerName={selectedFootballer.name}
          currentBid={selectedFootballer.value}
          onSubmit={handleBidSubmit}
        />
      )}
    </div>
  );
};

export default Market;
