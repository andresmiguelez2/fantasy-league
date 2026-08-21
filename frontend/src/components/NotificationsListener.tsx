import { useEffect, useRef } from "react";

import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import {
  fetchNotifications,
  getActiveLeagueId,
  getActivePlayerId,
  markNotificationsRead,
} from "@/lib/api";
import { isPushSupported, subscribeToPush, type PushMessage } from "@/lib/push";


const POLL_INTERVAL_MS = 30000;


export const NotificationsListener = () => {
  const { isAuthenticated } = useAuth();
  const { toast } = useToast();
  const seenIdsRef = useRef<Set<number>>(new Set());
  const subscribedContextRef = useRef<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      seenIdsRef.current.clear();
      subscribedContextRef.current = null;
      return;
    }

    if (!isPushSupported()) {
      return;
    }

    const maybeSubscribe = async () => {
      const playerId = getActivePlayerId();
      const leagueId = getActiveLeagueId();
      if (!playerId || !leagueId) {
        return;
      }

      const contextKey = `${playerId}:${leagueId}`;
      if (subscribedContextRef.current === contextKey) {
        return;
      }

      const subscribed = await subscribeToPush();
      if (subscribed) {
        subscribedContextRef.current = contextKey;
      }
    };

    maybeSubscribe();
    // Player/league ids resolve asynchronously right after login or league
    // switch, so retry once before giving up until the next context change.
    const timeoutId = window.setTimeout(maybeSubscribe, 4000);
    return () => window.clearTimeout(timeoutId);
  }, [isAuthenticated]);

  useEffect(() => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) {
      return;
    }

    const onServiceWorkerMessage = (event: MessageEvent) => {
      const data = event.data as PushMessage | null;
      if (!data || data.kind !== "push" || !data.title || !data.message) {
        return;
      }

      toast({
        title: data.title,
        description: data.message,
      });
    };

    navigator.serviceWorker.addEventListener("message", onServiceWorkerMessage);
    return () =>
      navigator.serviceWorker.removeEventListener("message", onServiceWorkerMessage);
  }, [toast]);

  useEffect(() => {
    if (!isAuthenticated) {
      return;
    }

    let cancelled = false;

    const pollNotifications = async () => {
      const playerId = getActivePlayerId();
      const leagueId = getActiveLeagueId();
      if (!playerId || !leagueId) {
        return;
      }

      try {
        const notifications = await fetchNotifications(playerId, {
          unreadOnly: true,
          limit: 20,
        });

        if (cancelled || notifications.length === 0) {
          return;
        }

        const unseen = notifications
          .filter((notification) => !seenIdsRef.current.has(notification.id))
          .sort((a, b) => a.id - b.id);

        if (!unseen.length) {
          return;
        }

        for (const notification of unseen) {
          toast({
            title: notification.title,
            description: notification.message,
          });

          if (typeof window !== "undefined" && "Notification" in window && Notification.permission === "granted") {
            new Notification(notification.title, {
              body: notification.message,
              tag: `fl-notification-${notification.id}`,
            });
          }

          seenIdsRef.current.add(notification.id);
        }

        await markNotificationsRead(
          unseen.map((notification) => notification.id),
          playerId,
        );
      } catch (error) {
        console.error("Failed to poll notifications:", error);
      }
    };

    pollNotifications();
    const intervalId = window.setInterval(pollNotifications, POLL_INTERVAL_MS);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [isAuthenticated, toast]);

  return null;
};
