import { useEffect, useRef } from "react";

import { useAuth } from "@/contexts/AuthContext";
import { useToast } from "@/hooks/use-toast";
import {
  fetchNotifications,
  getActiveLeagueId,
  getActivePlayerId,
  markNotificationsRead,
} from "@/lib/api";


const POLL_INTERVAL_MS = 30000;


export const NotificationsListener = () => {
  const { isAuthenticated } = useAuth();
  const { toast } = useToast();
  const seenIdsRef = useRef<Set<number>>(new Set());

  useEffect(() => {
    if (!isAuthenticated) {
      seenIdsRef.current.clear();
      return;
    }

    if (typeof window === "undefined" || !("Notification" in window)) {
      return;
    }

    if (Notification.permission === "default") {
      Notification.requestPermission().catch(() => null);
    }
  }, [isAuthenticated]);

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
