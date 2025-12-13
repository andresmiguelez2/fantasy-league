import { Header } from "@/components/Header";
import { NavigationTabs } from "@/components/NavigationTabs";
import { PlayerInfoRibbon } from "@/components/PlayerInfoRibbon";

const OutgoingBids = () => {
  return (
    <div className="min-h-screen bg-background">
      <Header />
      <NavigationTabs />
      
      <main className="container mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="max-w-4xl mx-auto">
          <h1 className="text-3xl font-bold mb-6">Outgoing Bids</h1>
          <p className="text-muted-foreground">Coming soon...</p>
        </div>
      </main>

      <PlayerInfoRibbon />
    </div>
  );
};

export default OutgoingBids;
