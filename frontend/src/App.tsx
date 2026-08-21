import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import { LeagueGuard } from "@/components/LeagueGuard";
import { NotificationsListener } from "@/components/NotificationsListener";
import Login from "./pages/Login";
import Landing from "./pages/Landing";
import League from "./pages/League";
import JoinLeague from "./pages/JoinLeague";
import Squad from "./pages/Squad";
import Lineup from "./pages/Lineup";
import Fixtures from "./pages/Fixtures";
import Market from "./pages/Market";
import IncomingBids from "./pages/IncomingBids";
import OutgoingBids from "./pages/OutgoingBids";
import FutureBids from "./pages/FutureBids";
import MarketHistory from "./pages/MarketHistory";
import FootballerInfo from "./pages/FootballerInfo";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <TooltipProvider>
      <Toaster />
      <Sonner />
      <BrowserRouter>
        <AuthProvider>
          <NotificationsListener />
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/join/:inviteCode" element={<JoinLeague />} />
            <Route path="/" element={<ProtectedRoute><Landing /></ProtectedRoute>} />
            <Route path="/league/:leagueId" element={<ProtectedRoute><League /></ProtectedRoute>} />
            <Route path="/squad" element={<ProtectedRoute><LeagueGuard><Squad /></LeagueGuard></ProtectedRoute>} />
            <Route path="/squad/:playerId" element={<ProtectedRoute><LeagueGuard><Squad /></LeagueGuard></ProtectedRoute>} />
            <Route path="/lineup" element={<ProtectedRoute><LeagueGuard><Lineup /></LeagueGuard></ProtectedRoute>} />
            <Route path="/fixtures" element={<ProtectedRoute><LeagueGuard><Fixtures /></LeagueGuard></ProtectedRoute>} />
            <Route path="/market" element={<ProtectedRoute><LeagueGuard><Market /></LeagueGuard></ProtectedRoute>} />
            <Route path="/market/incoming" element={<ProtectedRoute><LeagueGuard><IncomingBids /></LeagueGuard></ProtectedRoute>} />
            <Route path="/market/outgoing" element={<ProtectedRoute><LeagueGuard><OutgoingBids /></LeagueGuard></ProtectedRoute>} />
            <Route path="/market/future" element={<ProtectedRoute><LeagueGuard><FutureBids /></LeagueGuard></ProtectedRoute>} />
            <Route path="/market/history" element={<ProtectedRoute><LeagueGuard><MarketHistory /></LeagueGuard></ProtectedRoute>} />
            <Route path="/footballer-info" element={<ProtectedRoute><LeagueGuard><FootballerInfo /></LeagueGuard></ProtectedRoute>} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
