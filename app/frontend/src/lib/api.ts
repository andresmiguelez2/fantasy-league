// Mock API functions - Replace these endpoints with your actual API URLs

export interface League {
  id: string;
  name: string;
}

export interface Player {
  id: number;
  name: string;
  points: number;
  team_value: number;
}

export interface Footballer {
  id: number;
  name: string;
  team: string;
  value: number;
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
}

// Simulate API delay
const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const fetchLeagues = async (): Promise<League[]> => {
  await delay(800);
  // TODO: Replace with actual API call
  // const response = await fetch('YOUR_API_ENDPOINT/leagues');
  // return response.json();
  
  return [
    { id: '1', name: 'League 1' },
    { id: '2', name: 'League 2' },
    { id: '3', name: 'League 3' },
  ];
};

export const fetchLeaderboard = async (): Promise<Player[]> => {
  const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/leaderboard/`);
  const data = await response.json();
  
  return data.leaderboard.map((player: any[]) => ({
    id: player[0],
    name: player[1],
    points: player[2],
    team_value: player[3],
  }));
};

export const fetchSquadFootballers = async (playerId: string): Promise<Footballer[]> => {
  const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/squads/${playerId}`);
  const data = await response.json();
  
  // Transform the array format to objects
  return data.footballers.map((footballer: any[]) => ({
    id: footballer[0],
    name: footballer[1],
    team: footballer[2],
    value: footballer[3],
    onMarket: footballer[4],
    onMarketSince: footballer[5],
  }));
};

export const fetchMarketFootballers = async (playerId: string): Promise<MarketFootballer[]> => {
  await delay(800);

  const response = await fetch(`${import.meta.env.VITE_BACKEND_URL}/market/${playerId}`);
  const data = await response.json();
  
  // Transform the array format to objects
  return data.footballers.map((footballer: any[]) => ({
    id: footballer[0],
    name: footballer[1],
    team: footballer[2],
    value: footballer[3],
    onMarket: footballer[4],
    onMarketSince: footballer[5],
  }));
};

export const placeBid = async (footballerId: number, amount: number): Promise<void> => {
  await delay(500);
  // TODO: Replace with actual API call
  // await fetch('YOUR_API_ENDPOINT/bid', {
  //   method: 'POST',
  //   body: JSON.stringify({ footballerId, amount })
  // });
  
  console.log(`Bid placed: ${footballerId} - €${amount}`);
};
