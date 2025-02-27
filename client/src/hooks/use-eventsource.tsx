import { useEffect, useState } from "react";

interface EventSourceOptions {
  withCredentials?: boolean;
  onOpen?: (event: Event) => void;
  onError?: (error: Event) => void;
}

export function useEventSource<T = any>(
  url: string,
  options: EventSourceOptions = {}
) {
  const [data, setData] = useState<T[]>([]);
  const [status, setStatus] = useState<"connecting" | "open" | "closed">(
    "connecting"
  );
  const [error, setError] = useState<Event | null>(null);

  useEffect(() => {
    if (!url) return;

    const eventSource = new EventSource(url, {
      withCredentials: options.withCredentials || false,
    });

    eventSource.onopen = (event) => {
      setStatus("open");
      if (options.onOpen) options.onOpen(event);
    };

    eventSource.onmessage = (event) => {
      try {
        const parsedData = JSON.parse(event.data);
        setData((prev) => [...prev, parsedData]);
      } catch (e) {
        // If not JSON, add as string
        setData((prev) => [...prev, event.data as unknown as T]);
      }
    };

    eventSource.onerror = (event) => {
      setError(event);
      setStatus("closed");
      eventSource.close();
      if (options.onError) options.onError(event);
    };

    return () => {
      eventSource.close();
      setStatus("closed");
    };
  }, [url, options.withCredentials]);

  return { data, status, error, clearData: () => setData([]) };
}
