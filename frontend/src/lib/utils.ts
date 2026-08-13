import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const BID_EXPIRATION_DAYS = 7;

export interface RemainingTime {
  days: number;
  hours: number;
  minutes: number;
  seconds: number;
  isExpired: boolean;
  totalSeconds: number;
}

export function calculateRemainingTime(bidTimestamp: string): RemainingTime {
  const bidDate = new Date(bidTimestamp);
  const expirationDate = new Date(bidDate.getTime() + BID_EXPIRATION_DAYS * 24 * 60 * 60 * 1000);
  const now = new Date();

  const totalSeconds = Math.floor((expirationDate.getTime() - now.getTime()) / 1000);
  const isExpired = totalSeconds <= 0;

  if (isExpired) {
    return { days: 0, hours: 0, minutes: 0, seconds: 0, isExpired: true, totalSeconds: 0 };
  }

  const days = Math.floor(totalSeconds / (24 * 60 * 60));
  const remaining = totalSeconds % (24 * 60 * 60);
  const hours = Math.floor(remaining / (60 * 60));
  const minutes = Math.floor((remaining % (60 * 60)) / 60);
  const seconds = remaining % 60;

  return { days, hours, minutes, seconds, isExpired: false, totalSeconds };
}

export function formatRemainingTime(remainingTime: RemainingTime): string {
  if (remainingTime.isExpired) {
    return "Expired";
  }
  const pad = (num: number) => String(num).padStart(2, '0');
  return `${remainingTime.days}d ${pad(remainingTime.hours)}:${pad(remainingTime.minutes)}:${pad(remainingTime.seconds)}`;
}
