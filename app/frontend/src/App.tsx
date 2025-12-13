import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import Landing from "./pages/Landing";
import League from "./pages/League";
import Squad from "./pages/Squad";
import Lineup from "./pages/Lineup";
import Market from "./pages/Market";
import IncomingBids from "./pages/IncomingBids";
import OutgoingBids from "./pages/OutgoingBids";
import FootballerInfo from "./pages/FootballerInfo";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/league/:leagueId" element={<League />} />
          <Route path="/squad" element={<Squad />} />
          <Route path="/squad/:playerId" element={<Squad />} />
          <Route path="/lineup" element={<Lineup />} />
          <Route path="/market" element={<Market />} />
          <Route path="/market/incoming" element={<IncomingBids />} />
          <Route path="/market/outgoing" element={<OutgoingBids />} />
          <Route path="/footballer-info" element={<FootballerInfo />} />
          <Route path="*" element={<NotFound />} />
        </Routes>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
