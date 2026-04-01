// API functions

export interface League {
  id: string;
  name: string;
}

export interface Player {
  id: number;
  name: string;
  budget: number;
  points: number;
  team_value: number;
}

export interface Footballer {
  id: number;
  name: string;
  team: string;
  value: number;
  totalPoints: number;
  averagePoints: number | string;
  onMarket: boolean;
  onMarketSince: string | null;
}

export interface MarketFootballer {
  id: number;
  name: string;
  value: number;
  ownerId: string;
  onMarketSince: string;
  bidAmount: number;
  averagePoints: number | string;
  totalPoints: number;
}

export const BACKEND_URL = import.meta.env.VITE_BACKEND_URL || `${window.location.protocol}//${window.location.hostname}:8000`;

const ACTIVE_LEAGUE_KEY = 'activeLeagueId';

export const setActiveLeagueId = (leagueId: string) => {
  if (typeof window === 'undefined') {
    return;
  }

  localStorage.setItem(ACTIVE_LEAGUE_KEY, leagueId);
};

export const getActiveLeagueId = (): string | null => {
  if (typeof window === 'undefined') {
    return null;
  }

  return localStorage.getItem(ACTIVE_LEAGUE_KEY);
};

const withLeagueId = (params: Record<string, string>) => {
  const leagueId = getActiveLeagueId();
  if (!leagueId) {
    throw new Error('No active league selected');
  }
  const searchParams = new URLSearchParams({
    ...params,
    league_id: leagueId,
  });

  return searchParams.toString();
};

const getAuthToken = (): string | null =>
  typeof window !== 'undefined' ? localStorage.getItem('token') : null;

const getCurrentUserId = (): string | null => {
  if (typeof window === 'undefined') return null;
  const userStr = localStorage.getItem('user');
  return userStr ? (JSON.parse(userStr) as { id?: number })?.id?.toString() ?? null : null;
};

export const fetchLeagues = async (playerId?: string): Promise<League[]> => {
  try {
    const token = getAuthToken();
    const headers = token ? { Authorization: `Bearer ${token}` } : undefined;

    // Prefer user_id so that all leagues (across multiple players) are returned
    const userId = getCurrentUserId();

    if (userId) {
      try {
        const query = new URLSearchParams({ user_id: userId }).toString();
        const response = await fetch(`${BACKEND_URL}/leagues?${query}`, { headers });
        if (!response.ok) {
          throw new Error(`Failed to fetch leagues by user_id (${response.status})`);
        }
        const data = await response.json();
        if (data.status === 'success') {
          return (data.leagues as { id: number; name: string }[]).map((league) => ({
            id: String(league.id),
            name: league.name,
          }));
        }
      } catch {
        // Fall through to player_id fallback below
      }
    }

    // Fallback: use player_id (single-league behaviour / pre-migration)
    const resolvedPlayerId = playerId ?? (typeof window !== 'undefined' ? localStorage.getItem('playerId') : null);
    if (!resolvedPlayerId) {
      return [];
    }

    const query = new URLSearchParams({ player_id: resolvedPlayerId }).toString();
    const response = await fetch(`${BACKEND_URL}/leagues?${query}`, { headers });
    if (!response.ok) {
      throw new Error(`Failed to fetch leagues by player_id (${response.status})`);
    }
    const data = await response.json();
    return (data.leagues as { id: number; name: string }[]).map((league) => ({
      id: String(league.id),
      name: league.name,
    }));
  } catch (error) {
    console.error('Failed to fetch leagues:', error);
    return [];
  }
};

export const createLeague = async (leagueName: string, playerName: string): Promise<{ status: string; league?: { id: number; name: string }; player_id?: number; detail?: string }> => {
  const token = getAuthToken();
  if (!token) {
    throw new Error('Not authenticated');
  }

  const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/leagues`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ league_name: leagueName, player_name: playerName }),
  });
  return response.json();
};

export const fetchPlayerNames = async (): Promise<string[]> => {
  try {
    const token = getAuthToken();
    if (!token) return [];

    const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/leagues/player-names`, {
      headers: { 'Authorization': `Bearer ${token}` },
    });
    const data = await response.json();
    return (data.names as string[]) ?? [];
  } catch (error) {
    console.error('Failed to fetch player names:', error);
    return [];
  }
};

export const fetchLeaderboard = async (fixtureId: string = 'total'): Promise<Player[]> => {
  const response = await fetch(`${BACKEND_URL}/leaderboard/${fixtureId}?${withLeagueId({})}`);
  const data = await response.json();
  
  return data.leaderboard.map((player: any[]) => ({
    id: player[0],
    name: player[1],
    points: player[2],
    team_value: player[3],
  }));
};

export const fetchSquadFootballers = async (playerId: string): Promise<Footballer[]> => {
  const response = await fetch(`${BACKEND_URL}/squad/${playerId}?${withLeagueId({})}`);
  const data = await response.json();
  
  // Transform the array format to objects
  return data.footballers.map((footballer: any[]) => ({
    id: footballer[0],
    name: footballer[1],
    team: footballer[2],
    value: footballer[3],
    totalPoints: footballer[4],
    averagePoints: footballer[5],
    onMarket: footballer[6],
    onMarketSince: footballer[7],
  }));
};

export const fetchMarketFootballers = async (playerId: string): Promise<MarketFootballer[]> => {
  const response = await fetch(`${BACKEND_URL}/market/${playerId}?${withLeagueId({})}`);
  const data = await response.json();
  
  // Transform the array format to objects
  return data.footballers.map((footballer: any[]) => ({
    id: footballer[0],
    name: footballer[1],
    value: footballer[2],
    ownerId: footballer[3],
    onMarketSince: footballer[4],
    bidAmount: footballer[5],
    averagePoints: footballer[6],
    totalPoints: footballer[7],
  }));
};

export interface PlayerInfo {
  id: number;
  name: string;
  points: number;
  budget: number;
}

// Return a `Player` shape for UI convenience (maps budget -> team_value)
export const fetchPlayerInfo = async (playerId: string): Promise<Player> => {
  const response = await fetch(`${BACKEND_URL}/player/${playerId}?${withLeagueId({})}`);
  const data = await response.json();

  // The API returns [id, name, budget, points]
  const arr = Array.isArray(data)
    ? data
    : Array.isArray(data?.player)
    ? data.player
    : null;

  if (!arr || arr.length < 4) {
    throw new Error('Unexpected player response format');
  }

  const [id, name, budget, points] = arr;

  // Map API [id, name, budget, points] -> Player { id, name, points, team_value }
  return {
    id: Number(id),
    name: String(name),
    points: Number(points ?? 0),
    budget: Number(budget ?? 0),
    team_value: Number(budget ?? 0),
  };
};

export const placeBid = async (
  footballerId: number,
  playerId: string,
  amount: number
): Promise<any> => {
  const leagueId = getActiveLeagueId();
  if (!leagueId) {
    throw new Error('No active league selected');
  }
  const res = await fetch(`${BACKEND_URL}/market/bid`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      footballer_id: footballerId,
      player_id: playerId,
      bid_amount: amount,
      league_id: parseInt(leagueId),
    }),
  });

  // Try to parse JSON response; if none, return status info
  const text = await res.text();
  if (!text) {
    return { status: res.status, ok: res.ok };
  }

  try {
    return JSON.parse(text);
  } catch {
    // not JSON, return raw text
    return { status: res.status, ok: res.ok, text };
  }
};

export interface FootballerInfo {
  name: string;
  team: string;
  total_points: number;
  average_points: number;
  market_value: number;
  market_details: { date: string; value: number }[];
  fixture_breakdown: { fixture: number; points: number }[];
  owner_id: number | null;
  owner_name: string | null;
}

export interface FixtureDetail {
  fixture: number;
  breakdown: Record<string, { value: number | null; points: number }>;
}

export const fetchFootballerInfo = async (footballerId: number): Promise<FootballerInfo> => {
  const response = await fetch(
    `${BACKEND_URL}/footballer/${footballerId}?${withLeagueId({})}`
  );
  const data = await response.json();
  return data.footballer_info;
};

export const fetchFixtureDetail = async (footballerId: number, fixture: number): Promise<FixtureDetail> => {
  const response = await fetch(`${BACKEND_URL}/footballer/fixture_detail/${footballerId}?fixture=${fixture}`);
  const data = await response.json();
  return data.fixture_detail;
};

export const fetchOpenedFixtures = async (): Promise<number[]> => {
  const response = await fetch(`${BACKEND_URL}/general/opened_fixtures?${withLeagueId({})}`);
  const data = await response.json();
  return data.opened_fixtures;
};

export const fetchPlayerFixtures = async (playerId: string): Promise<number[]> => {
  const response = await fetch(`${BACKEND_URL}/player/fixtures/${playerId}?${withLeagueId({})}`);
  const data = await response.json();
  return data.fixtures || [];
};

export const fetchFixtureLineup = async (playerId: string, fixtureN: number): Promise<{ lineup: number[]; lineupFootballers: number[][] }> => {
  const response = await fetch(
    `${BACKEND_URL}/player/fixture_lineup/${playerId}?${withLeagueId({ fixture_n: fixtureN.toString() })}`
  );
  const data = await response.json();
  return {
    lineup: data.lineup || [],
    lineupFootballers: data.lineup_footballers || []
  };
};

export const fetchFootballerFixturePoints = async (footballerId: number, fixture: number): Promise<number | null> => {
  const response = await fetch(`${BACKEND_URL}/footballer/fixture_points/${footballerId}?fixture=${fixture}`);
  const data = await response.json();
  return data.points ?? null;
};

export const fetchAllFootballers = async (
  page: number = 1,
  limit: number = 25,
  sortBy: 'name' | 'points' | 'value' = 'name',
  sortOrder: 'asc' | 'desc' = 'asc',
  search: string = ''
): Promise<MarketFootballer[]> => {
  const leagueId = getActiveLeagueId();
  if (!leagueId) {
    throw new Error('No active league selected');
  }
  const params = new URLSearchParams({
    page: page.toString(),
    limit: limit.toString(),
    sort: sortBy,
    invert: sortOrder === 'desc' ? 'true' : 'false',
    search: search,
    league_id: leagueId,
  });
  
  const response = await fetch(
    `${BACKEND_URL}/footballers?${params}`
  );
  const data = await response.json();
  
  // Map to MarketFootballer format
  return data.footballers.map((footballer: any[]) => ({
    id: footballer[0],
    name: footballer[1],
    value: footballer[2],
    ownerId: footballer[3] || '',
    onMarketSince: footballer[4] || '',
    bidAmount: footballer[5] || 0,
    averagePoints: footballer[6],
    totalPoints: footballer[7],
  }));
};

export interface LineupFormation {
  status: string;
  lineup: number[];
}

export const fetchLineupFormation = async (playerId: string): Promise<number[]> => {
  const response = await fetch(`${BACKEND_URL}/player/lineup/${playerId}?${withLeagueId({})}`);
  const data: LineupFormation = await response.json();
  return data.lineup;
};

export const fetchLineupFootballers = async (playerId: string): Promise<number[][]> => {
  const response = await fetch(
    `${BACKEND_URL}/player/lineup_footballers/${playerId}?${withLeagueId({})}`
  );
  const data = await response.json();
  return data.lineup_footballers || [];
};

export const fetchFootballerShortName = async (footballerId: number): Promise<string> => {
  const response = await fetch(`${BACKEND_URL}/footballer/short_name/${footballerId}`);
  const data = await response.json();
  return data.name;
};

export interface Substitute {
  id: number;
  name: string;
  value: number;
  totalPoints: number;
  averagePoints: number;
}

export const fetchAvailableSubs = async (playerId: string, position: number): Promise<Substitute[]> => {
  const response = await fetch(
    `${BACKEND_URL}/player/available_subs/${playerId}?${withLeagueId({ position: position.toString() })}`
  );
  const data = await response.json();
  
  return data.substitutes.map((sub: any[]) => ({
    id: sub[0],
    name: sub[1],
    value: sub[2],
    totalPoints: sub[3],
    averagePoints: sub[4],
  }));
};

export const setLineup = async (playerId: string, footballerId: number, onLineup: boolean): Promise<boolean> => {
  const leagueId = getActiveLeagueId();
  if (!leagueId) {
    throw new Error('No active league selected');
  }
  const response = await fetch(`${BACKEND_URL}/footballer/set_lineup/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      player_id: parseInt(playerId),
      footballer_id: footballerId,
      league_id: parseInt(leagueId),
      on_lineup: onLineup,
    }),
  });
  const data = await response.json();
  return data.status === "success";
};

export interface IncomingBid {
  bidId: number;
  timestamp: string;
  footballerId: number;
  bidderId: number;
  footballerName: string;
  amount: number;
}

export const fetchIncomingBids = async (playerId: string): Promise<IncomingBid[]> => {
  const response = await fetch(`${BACKEND_URL}/market/incoming_bids/${playerId}?${withLeagueId({})}`);
  const data = await response.json();
  
  return data.bids.map((bid: any[]) => ({
    bidId: bid[0],
    timestamp: bid[1],
    footballerId: bid[2],
    bidderId: bid[3],
    footballerName: bid[4],
    amount: bid[5],
  }));
};

export const replyToBid = async (bidId: number, accept: boolean): Promise<boolean> => {
  const response = await fetch(
    `${BACKEND_URL}/market/reply_to_bid/${bidId}?accept=${accept}`,
    { method: 'POST' }
  );
  const data = await response.json();
  return data.status === "success";
};

export interface OutgoingBid {
  bidId: number;
  timestamp: string;
  footballerId: number;
  ownerId: number | null;
  footballerName: string;
  amount: number;
}

export const fetchOutgoingBids = async (playerId: string): Promise<OutgoingBid[]> => {
  const response = await fetch(`${BACKEND_URL}/market/outgoing_bids/${playerId}?${withLeagueId({})}`);
  const data = await response.json();
  
  return data.bids.map((bid: any[]) => ({
    bidId: bid[0],
    timestamp: bid[1],
    footballerId: bid[2],
    ownerId: bid[3],
    footballerName: bid[4],
    amount: bid[5],
  }));
};

export const submitBid = async (footballerId: number, playerId: string, amount: number): Promise<boolean> => {
  const leagueId = getActiveLeagueId();
  if (!leagueId) {
    throw new Error('No active league selected');
  }
  const response = await fetch(`${BACKEND_URL}/market/bid`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      footballer_id: footballerId,
      player_id: playerId,
      bid_amount: amount,
      league_id: parseInt(leagueId),
    }),
  });
  const data = await response.json();
  return data.status === "success";
};

export interface ReleaseClauseData {
  status: string;
  rc_available: boolean;
  release_clause: number;
  time_until_rc?: number;
  message?: string;
}

export interface PayReleaseClauseResponse {
  status: string;
  message?: string;
  ok?: boolean;
  text?: string;
}

export const fetchReleaseClauseData = async (footballerId: number): Promise<ReleaseClauseData> => {
  const response = await fetch(
    `${BACKEND_URL}/footballer/release_clause_data/${footballerId}?${withLeagueId({})}`
  );
  const data = await response.json();
  return data;
};

export const fetchMarketStatus = async (footballerId: number): Promise<boolean> => {
  const response = await fetch(
    `${BACKEND_URL}/footballer/market_status/${footballerId}?${withLeagueId({})}`
  );
  const data = await response.json();
  if (data.status !== "success") {
    throw new Error(data.message || "Failed to fetch market status");
  }
  return data.on_market;
};

export const changeMarketStatus = async (footballerId: number, onMarket: boolean): Promise<any> => {
  const response = await fetch(
    `${BACKEND_URL}/footballer/change_market_status/${footballerId}?${withLeagueId({ on_market: String(onMarket) })}`,
    { method: 'POST' }
  );
  return response.json();
};

export const payReleaseClause = async (footballerId: number, playerId: string): Promise<PayReleaseClauseResponse> => {
  const res = await fetch(`${BACKEND_URL}/market/pay_release_clause`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      footballer_id: footballerId,
      player_id: playerId,
    }),
  });

  const text = await res.text();
  if (!text) {
    return { status: res.status.toString(), ok: res.ok };
  }

  try {
    return JSON.parse(text);
  } catch {
    return { status: res.status.toString(), ok: res.ok, text };
  }
};
