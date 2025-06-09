import { AUTH_STORAGE_KEY } from "@/src/utils/constants";
import { EventSource } from "eventsource";
import { useCallback, useEffect, useState } from "react";

export function useEventSource<T = any>(url: string | null) {
  const [data, setData] = useState<T[]>([]);
  const [status, setStatus] = useState<"idle" | "connecting" | "open" | "closed">("idle");
  const [error, setError] = useState<Event | null>(null);
  // New state to control connection
  const [isConnected, setIsConnected] = useState(false);

  // Function to get auth headers
  const getAuthHeaders = useCallback(() => {
    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY);
      if (!stored) return {};

      const session = JSON.parse(stored);
      const token = session.access_token;

      if (token) {
        return { Authorization: `Bearer ${token}` };
      }
      return {};
    } catch {
      localStorage.removeItem(AUTH_STORAGE_KEY);
      return {};
    }
  }, []);

  // Start connection function
  const startConnection = useCallback(() => {
    setIsConnected(true);
    setData([]); // Clear any previous data
    setError(null);
  }, []);

  // Stop connection function
  const stopConnection = useCallback(() => {
    setIsConnected(false);
  }, []);

  // Reset everything function
  const reset = useCallback(() => {
    stopConnection();
    setData([]);
    setError(null);
    setStatus("idle");
  }, [stopConnection]);

  useEffect(() => {
    // Only connect if URL is provided AND isConnected is true
    if (!url || !isConnected) {
      if (isConnected && !url) {
        // If we're trying to connect but URL is missing
        setStatus("closed");
        setError(new Event("No URL provided"));
        setIsConnected(false);
      }
      return;
    }

    setStatus("connecting");

    // Get auth headers
    const headers = getAuthHeaders();

    const eventSource = new EventSource(url, {
      fetch: (input, init) =>
        fetch(input, {
          ...init,
          credentials: "include",
          headers: {
            ...(init?.headers as Record<string, string>),
            ...headers,
          } as HeadersInit,
        }),
    });

    eventSource.onopen = () => {
      setStatus("open");
    };

    eventSource.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        setData((prev) => [...prev, parsedData]);
      } catch {
        setData((prev) => [...prev, event.data as unknown as T]);
      }
    };

    eventSource.onerror = (event) => {
      setError(event);
      setStatus("closed");
      eventSource.close();
      setIsConnected(false); // Auto-disable connection on error
    };

    return () => {
      eventSource.close();
      setStatus("closed");
    };
  }, [url, isConnected, getAuthHeaders]);

  return {
    data,
    status,
    error,
    isConnected,
    startConnection,
    stopConnection,
    reset,
    clearData: () => setData([]),
  };
}
