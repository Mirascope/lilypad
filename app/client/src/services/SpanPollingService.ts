import { SpanPublic } from "@/src/types/types";
import { fetchRecentSpans, type RecentSpansResponse } from "@/src/utils/traces";

interface PollingOptions {
  projectUuid: string;
  interval?: number;
  onUpdate?: (spans: SpanPublic[]) => void;
  onError?: (error: Error) => void;
}

export class SpanPollingService {
  private intervalId: NodeJS.Timeout | null = null;
  private lastTimestamp: Date | null = null;
  private isPolling = false;

  /**
   * Start polling for new spans
   * @param options Polling configuration
   */
  start({ projectUuid, interval = 5000, onUpdate, onError }: PollingOptions) {
    if (this.isPolling) {
      console.warn("Polling is already active");
      return;
    }

    this.isPolling = true;
    this.lastTimestamp = new Date();

    // Initial poll
    this.poll(projectUuid, onUpdate, onError);

    // Set up interval for subsequent polls
    this.intervalId = setInterval(() => {
      this.poll(projectUuid, onUpdate, onError);
    }, interval);
  }

  /**
   * Stop polling
   */
  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.isPolling = false;
    this.lastTimestamp = null;
  }

  /**
   * Perform a single poll
   */
  private async poll(
    projectUuid: string,
    onUpdate?: (spans: SpanPublic[]) => void,
    onError?: (error: Error) => void
  ) {
    try {
      const data = await fetchRecentSpans(
        projectUuid,
        this.lastTimestamp?.toISOString()
      );
      
      if (data.spans && data.spans.length > 0) {
        onUpdate?.(data.spans);
      }

      // Update last timestamp for next poll
      this.lastTimestamp = new Date(data.timestamp);
    } catch (error) {
      console.error("Error polling for spans:", error);
      onError?.(error as Error);
    }
  }

  /**
   * Check if polling is currently active
   */
  isActive(): boolean {
    return this.isPolling;
  }
}

// Export a singleton instance
export const spanPollingService = new SpanPollingService();