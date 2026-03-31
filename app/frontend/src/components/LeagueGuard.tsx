import { Navigate } from 'react-router-dom';
import { getActiveLeagueId } from '@/lib/api';

interface LeagueGuardProps {
  children: React.ReactNode;
}

export const LeagueGuard = ({ children }: LeagueGuardProps) => {
  if (!getActiveLeagueId()) {
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};
