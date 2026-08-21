import { precacheAndRoute } from "workbox-precaching";

/// <reference lib="webworker" />
declare let self: ServiceWorkerGlobalScope;

precacheAndRoute(self.__WB_MANIFEST);

interface PushPayload {
  type?: string;
  title?: string;
  message?: string;
  url?: string;
}

self.addEventListener("push", (event: PushEvent) => {
  let payload: PushPayload = {};
  try {
    payload = event.data ? event.data.json() : {};
  } catch {
    payload = { message: event.data ? event.data.text() : undefined };
  }

  const title = payload.title || "Fantasy League";
  event.waitUntil(
    (async () => {
      const clientList = await self.clients.matchAll({
        type: "window",
        includeUncontrolled: true,
      });
      for (const client of clientList) {
        if (client.visibilityState === "visible" && "focus" in client) {
          client.postMessage({ kind: "push", ...payload });
          return;
        }
      }
      await self.registration.showNotification(title, {
        body: payload.message,
        tag: `fl-push-${payload.type ?? "default"}`,
        icon: "pwa-192x192.png",
        badge: "pwa-192x192.png",
        data: { url: payload.url ?? "/" },
      });
    })(),
  );
});

self.addEventListener("notificationclick", (event: NotificationEvent) => {
  event.notification.close();
  const url: string = event.notification.data?.url ?? "/";

  event.waitUntil(
    (async () => {
      const clientList = await self.clients.matchAll({
        type: "window",
        includeUncontrolled: true,
      });
      for (const client of clientList) {
        if ("focus" in client) {
          await client.focus();
          return;
        }
      }
      if (self.clients.openWindow) {
        await self.clients.openWindow(url);
      }
    })(),
  );
});

self.addEventListener("message", (event) => {
  if (event.data === "SKIP_WAITING") {
    self.skipWaiting();
  }
});
