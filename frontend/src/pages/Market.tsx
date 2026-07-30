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
import { getActiveLeagueId, getActivePlayerId } from "@/lib/api";

const Market = () => {
  const { playerId } = useParams();
  const leagueId = getActiveLeagueId();
  const [footballers, setFootballers] = useState<MarketFootballer[]>([]);
  const [loading, setLoading] = useState(true);
  const [bidDialogOpen, setBidDialogOpen] = useState(false);
  const [infoDialogOpen, setInfoDialogOpen] = useState(false);
  const [selectedFootballer, setSelectedFootballer] = useState<MarketFootballer | null>(null);
  const [marketClosingTimestamp, setMarketClosingTimestamp] = useState<string | null>(null);
  const [remainingMarketTime, setRemainingMarketTime] = useState<string>('—');
  const { toast } = useToast();
  
  useEffect(() => {
    const loadFootballers = async () => {
      setLoading(true);
      try {
        const id = playerId || getActivePlayerId();
        if (!id) {
          setFootballers([]);
          return;
        }
        const data = await fetchMarketFootballers(id);
        setFootballers(data.footballers);
        setMarketClosingTimestamp(data.marketClosingTimestamp);
      } catch (error) {
        console.error('Failed to fetch market data:', error);
        setFootballers([]);
        setMarketClosingTimestamp(null);
      } finally {
        setLoading(false);
      }
    };
    
    loadFootballers();
  }, [playerId]);

  useEffect(() => {
    const updateRemainingTime = () => {
      if (!marketClosingTimestamp) {
        setRemainingMarketTime('Unavailable');
        return;
      }

      const diff = new Date(marketClosingTimestamp).getTime() - Date.now();
      if (diff <= 0) {
        setRemainingMarketTime('Closed');
        return;
      }

      const totalSeconds = Math.floor(diff / 1000);
      const hours = Math.floor(totalSeconds / 3600);
      const minutes = Math.floor((totalSeconds % 3600) / 60);
      const seconds = totalSeconds % 60;

      setRemainingMarketTime(
        `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds
          .toString()
          .padStart(2, '0')}`
      );
    };

    updateRemainingTime();
    const interval = setInterval(updateRemainingTime, 1000);
    return () => clearInterval(interval);
  }, [marketClosingTimestamp]);
  
  const handleBidClick = (footballer: MarketFootballer) => {
    setSelectedFootballer(footballer);
    setBidDialogOpen(true);
  };

  const handleFootballerClick = (footballer: MarketFootballer) => {
    setSelectedFootballer(footballer);
    setInfoDialogOpen(true);
  };
  
  const handleBidSubmit = async (amount: number, timestamp?: string | null) => {
    if (!selectedFootballer) return false;
    
    const id = playerId || getActivePlayerId();
    if (!id) {
      toast({
        description: 'Unable to place bid: no active player selected',
        variant: 'destructive',
      });
      return false;
    }
    const resp = await placeBid(selectedFootballer.id, id, amount, timestamp);
    const success = resp?.status === "success";
    const scheduledForFuture = timestamp && new Date(timestamp).getTime() > Date.now();

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
        : scheduledForFuture
          ? `Your bid of €${amount.toLocaleString()} for ${selectedFootballer.name} has been scheduled.`
          : `Your bid of €${amount.toLocaleString()} for ${selectedFootballer.name} has been placed.`),
      variant: success ? 'default' : 'destructive',
    });

    if (!success) {
      return false;
    }
    
    // Update the footballer's value with the new bid
    setFootballers(prev =>
      prev.map(f =>
        f.id === selectedFootballer.id
          ? { ...f, value: amount, bidAmount: amount === 0 || scheduledForFuture ? 0 : amount }
          : f
      )
    );

    return true;
  };
  
  return (
    <div className="min-h-screen bg-background pb-20">
      <Header showBackButton />
      <NavigationTabs leagueId={leagueId} />
      
      <main className="container mx-auto px-2 sm:px-6 lg:px-8 py-4 sm:py-8">
        {loading ? (
          <LoadingSkeleton type="footballers" />
        ) : (
          <div className="space-y-2 sm:space-y-3 max-w-2xl">
            <p className="text-sm text-muted-foreground pb-2">
              Market time remaining: <span className="font-medium text-foreground">{remainingMarketTime}</span>
            </p>
            {footballers.map((footballer) => (
              <FootballerCard
                key={footballer.id}
                id={footballer.id}
                name={footballer.name}
                owner={footballer.ownerId}
                value={footballer.value}
                currentBid={footballer.bidAmount}
                totalPoints={footballer.totalPoints}
                averagePoints={footballer.averagePoints}
                position={footballer.position}
                availability={footballer.availability}
                showBidButton={!footballer.isOwn}
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
            footballerValue={selectedFootballer.value}
            currentBid={selectedFootballer.bidAmount || undefined}
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
