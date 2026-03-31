import { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import { BACKEND_URL } from '@/lib/api';

interface User {
  id: number;        // User ID from the users table
  username: string;
  playerId: number;  // Associated player ID in the game
}

interface AuthContextType {
  user: User | null;
  token: string | null;
  login: (username: string, password: string) => Promise<boolean>;
  logout: () => void;
  isAuthenticated: boolean;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Load token from localStorage on mount and verify with server
  useEffect(() => {
    const storedToken = localStorage.getItem('token');

    if (!storedToken) {
      setIsLoading(false);
      return;
    }

    // Verify token and get fresh user data (including correct player_id) from server
    fetch(`${BACKEND_URL}/auth/me`, {
      headers: { Authorization: `Bearer ${storedToken}` },
    })
      .then(res => (res.ok ? res.json() : null))
      .then(data => {
        if (data) {
          const refreshedUser: User = {
            id: data.id,
            username: data.username,
            playerId: data.player_id,
          };
          setToken(storedToken);
          setUser(refreshedUser);
          localStorage.setItem('user', JSON.stringify(refreshedUser));
          localStorage.setItem('playerId', data.player_id.toString());
        } else {
          // Token is invalid or expired – clear stored session
          setToken(null);
          setUser(null);
          localStorage.removeItem('token');
          localStorage.removeItem('user');
          localStorage.removeItem('playerId');
        }
      })
      .catch(() => {
        // Network error – clear stored session so the user is prompted to log in
        setToken(null);
        setUser(null);
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        localStorage.removeItem('playerId');
      })
      .finally(() => setIsLoading(false));
  }, []);

  const login = async (username: string, password: string): Promise<boolean> => {
    try {
      const response = await fetch(`${BACKEND_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password }),
      });

      if (!response.ok) {
        return false;
      }

      const data = await response.json();
      
      const userData: User = {
        id: data.id,           // User ID from the users table
        username: data.username,
        playerId: data.player_id, // The player in the fantasy game
      };

      setToken(data.access_token);
      setUser(userData);
      
      // Store in localStorage
      localStorage.setItem('token', data.access_token);
      localStorage.setItem('user', JSON.stringify(userData));
      localStorage.setItem('playerId', data.player_id.toString());

      return true;
    } catch (error) {
      console.error('Login error:', error);
      return false;
    }
  };

  const logout = () => {
    // Clear state and localStorage
    // Note: JWT tokens are stateless, so invalidation is handled client-side
    setToken(null);
    setUser(null);
    localStorage.removeItem('token');
    localStorage.removeItem('user');
    localStorage.removeItem('playerId');
  };

  const value: AuthContextType = {
    user,
    token,
    login,
    logout,
    isAuthenticated: !!token && !!user,
    isLoading,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
