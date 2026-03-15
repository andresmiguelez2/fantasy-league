import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { AuthProvider } from "@/contexts/AuthContext";
import { ProtectedRoute } from "@/components/ProtectedRoute";
import Login from "./pages/Login";
import Landing from "./pages/Landing";
import League from "./pages/League";
import Squad from "./pages/Squad";
import Lineup from "./pages/Lineup";
import Fixtures from "./pages/Fixtures";
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
        <AuthProvider>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/" element={<ProtectedRoute><Landing /></ProtectedRoute>} />
            <Route path="/league/:leagueId" element={<ProtectedRoute><League /></ProtectedRoute>} />
            <Route path="/league/:leagueId/squad" element={<ProtectedRoute><Squad /></ProtectedRoute>} />
            <Route path="/league/:leagueId/squad/:playerId" element={<ProtectedRoute><Squad /></ProtectedRoute>} />
            <Route path="/league/:leagueId/lineup" element={<ProtectedRoute><Lineup /></ProtectedRoute>} />
            <Route path="/league/:leagueId/fixtures" element={<ProtectedRoute><Fixtures /></ProtectedRoute>} />
            <Route path="/league/:leagueId/market" element={<ProtectedRoute><Market /></ProtectedRoute>} />
            <Route path="/league/:leagueId/market/incoming" element={<ProtectedRoute><IncomingBids /></ProtectedRoute>} />
            <Route path="/league/:leagueId/market/outgoing" element={<ProtectedRoute><OutgoingBids /></ProtectedRoute>} />
            <Route path="/league/:leagueId/footballer-info" element={<ProtectedRoute><FootballerInfo /></ProtectedRoute>} />
            {/* Legacy routes for backward compatibility */}
            <Route path="/squad" element={<ProtectedRoute><Squad /></ProtectedRoute>} />
            <Route path="/squad/:playerId" element={<ProtectedRoute><Squad /></ProtectedRoute>} />
            <Route path="/lineup" element={<ProtectedRoute><Lineup /></ProtectedRoute>} />
            <Route path="/fixtures" element={<ProtectedRoute><Fixtures /></ProtectedRoute>} />
            <Route path="/market" element={<ProtectedRoute><Market /></ProtectedRoute>} />
            <Route path="/market/incoming" element={<ProtectedRoute><IncomingBids /></ProtectedRoute>} />
            <Route path="/market/outgoing" element={<ProtectedRoute><OutgoingBids /></ProtectedRoute>} />
            <Route path="/footballer-info" element={<ProtectedRoute><FootballerInfo /></ProtectedRoute>} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </AuthProvider>
      </BrowserRouter>
    </TooltipProvider>
  </QueryClientProvider>
);

export default App;
