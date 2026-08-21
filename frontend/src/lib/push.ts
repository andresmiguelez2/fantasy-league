import {
  getVapidPublicKey,
  subscribePush,
  getActiveLeagueId,
  getActivePlayerId,
} from "@/lib/api";

export interface PushMessage {
  kind?: string;
  type?: string;
  title?: string;
  message?: string;
  url?: string;
}

export const isPushSupported = (): boolean =>
  typeof window !== "undefined" &&
  "serviceWorker" in navigator &&
  "PushManager" in window &&
  "Notification" in window;

const urlBase64ToUint8Array = (base64String: string): Uint8Array => {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const raw = atob(base64);
  return Uint8Array.from(raw, (char) => char.charCodeAt(0));
};

/**
 * Requests notification permission (if needed) and registers this device's
 * Web Push subscription with the backend for the active player/league.
 * Best-effort: resolves to false when push is unavailable or rejected.
 */
export const subscribeToPush = async (): Promise<boolean> => {
  if (!isPushSupported()) {
    return false;
  }

  const playerId = getActivePlayerId();
  const leagueId = getActiveLeagueId();
  if (!playerId || !leagueId) {
    return false;
  }

  let permission = Notification.permission;
  if (permission === "default") {
    permission = await Notification.requestPermission();
  }
  if (permission !== "granted") {
    return false;
  }

  const publicKey = await getVapidPublicKey();
  if (!publicKey) {
    console.warn("Push notifications unavailable: server VAPID key missing");
    return false;
  }

  const registration = await navigator.serviceWorker.ready;
  let subscription = await registration.pushManager.getSubscription();
  if (!subscription) {
    try {
      subscription = await registration.pushManager.subscribe({
        userVisibleOnly: true,
        applicationServerKey: urlBase64ToUint8Array(publicKey),
      });
    } catch (error) {
      console.warn("Push subscription failed:", error);
      return false;
    }
  }

  const json = subscription.toJSON() as {
    endpoint?: string;
    keys?: { p256dh?: string; auth?: string };
  };
  if (!json.endpoint || !json.keys?.p256dh || !json.keys?.auth) {
    return false;
  }

  try {
    return await subscribePush(playerId, leagueId, {
      endpoint: json.endpoint,
      keys: { p256dh: json.keys.p256dh, auth: json.keys.auth },
    });
  } catch (error) {
    console.warn("Failed to register push subscription:", error);
    return false;
  }
};
