// Mock API functions - Replace these endpoints with your actual API URLs

export interface League {
  id: string;
  name: string;
}

export interface Player {
  id: string;
  name: string;
  points: number;
  value: number;
}

export interface Footballer {
  id: number;
  name: string;
  team: string;
  value: number;
  onMarket: boolean;
  onMarketSince: string | null;
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

export const fetchPlayers = async (leagueId: string): Promise<Player[]> => {
  await delay(800);
  // TODO: Replace with actual API call
  // const response = await fetch(`YOUR_API_ENDPOINT/leagues/${leagueId}/players`);
  // return response.json();
  
  return [
    { id: '1', name: 'Player 1', points: 74, value: 145569014 },
    { id: '2', name: 'Player 2', points: 57, value: 140569014 },
    { id: '3', name: 'Player 3', points: 54, value: 145569014 },
    { id: '4', name: 'Player 4', points: 21, value: 145569014 },
  ];
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

export const fetchMarketFootballers = async (): Promise<Footballer[]> => {
  await delay(800);
  // TODO: Replace with actual API call
  // const response = await fetch('YOUR_API_ENDPOINT/market');
  // return response.json();
  
  return [
    { id: 1, name: 'Footballer 1', team: 'Team A', value: 587000, onMarket: true, onMarketSince: new Date().toISOString() },
    { id: 2, name: 'Footballer 2', team: 'Team B', value: 450000, onMarket: true, onMarketSince: null },
    { id: 3, name: 'Footballer 3', team: 'Team C', value: 320000, onMarket: true, onMarketSince: null },
    { id: 4, name: 'Footballer 4', team: 'Team D', value: 680000, onMarket: true, onMarketSince: null },
    { id: 5, name: 'Footballer 5', team: 'Team E', value: 520000, onMarket: true, onMarketSince: null },
  ];
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
