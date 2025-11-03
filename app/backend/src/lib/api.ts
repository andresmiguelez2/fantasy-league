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
  id: string;
  name: string;
  currentBid?: number;
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

export const fetchSquadFootballers = async (): Promise<Footballer[]> => {
  await delay(800);
  // TODO: Replace with actual API call
  // const response = await fetch('YOUR_API_ENDPOINT/squad');
  // return response.json();
  
  return [
    { id: '1', name: 'Footballer 1' },
    { id: '2', name: 'Footballer 2' },
    { id: '3', name: 'Footballer 3' },
    { id: '4', name: 'Footballer 4' },
    { id: '5', name: 'Footballer 5' },
  ];
};

export const fetchMarketFootballers = async (): Promise<Footballer[]> => {
  await delay(800);
  // TODO: Replace with actual API call
  // const response = await fetch('YOUR_API_ENDPOINT/market');
  // return response.json();
  
  return [
    { id: '1', name: 'Footballer 1', currentBid: 587000 },
    { id: '2', name: 'Footballer 2' },
    { id: '3', name: 'Footballer 3' },
    { id: '4', name: 'Footballer 4' },
    { id: '5', name: 'Footballer 5' },
  ];
};

export const placeBid = async (footballerId: string, amount: number): Promise<void> => {
  await delay(500);
  // TODO: Replace with actual API call
  // await fetch('YOUR_API_ENDPOINT/bid', {
  //   method: 'POST',
  //   body: JSON.stringify({ footballerId, amount })
  // });
  
  console.log(`Bid placed: ${footballerId} - €${amount}`);
};
