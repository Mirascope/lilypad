import { SpanPublic } from "@/src/types/types";
import { fetchRecentSpans, type RecentSpansResponse } from "@/src/utils/traces";

interface PollingOptions {
  projectUuid: string;
  interval?: number;
  onUpdate?: (spans: SpanPublic[]) => void;
  onError?: (error: Error) => void;
  onMaxErrors?: () => void;
}

// Configuration constants
const MAX_CONSECUTIVE_ERRORS = 3;
const ERROR_BACKOFF_MULTIPLIER = 2;
const MAX_BACKOFF_MS = 30000; // 30 seconds max backoff

export class SpanPollingService {
  private intervalId: NodeJS.Timeout | null = null;
  private lastTimestamp: Date | null = null;
  private isPolling = false;
  private isPaused = false;
  private errorCount = 0;
  private currentInterval: number = 5000;
  private baseInterval: number = 5000;
  private options: PollingOptions | null = null;
  private seenSpanIds = new Set<string>();

  /**
   * Start polling for new spans
   * @param options Polling configuration
   */
  start(options: PollingOptions) {
    if (this.isPolling) {
      console.warn("Polling is already active");
      return;
    }

    this.options = options;
    this.isPolling = true;
    this.isPaused = false;
    this.errorCount = 0;
    this.lastTimestamp = new Date();
    this.baseInterval = options.interval || 5000;
    this.currentInterval = this.baseInterval;
    this.seenSpanIds.clear();

    // Initial poll
    this.poll();

    // Set up interval for subsequent polls
    this.scheduleNextPoll();
  }

  /**
   * Stop polling completely
   */
  stop() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
    this.isPolling = false;
    this.isPaused = false;
    this.lastTimestamp = null;
    this.errorCount = 0;
    this.options = null;
    this.seenSpanIds.clear();
  }

  /**
   * Pause polling (e.g., when tab is hidden)
   */
  pause() {
    if (this.isPolling && !this.isPaused) {
      this.isPaused = true;
      if (this.intervalId) {
        clearInterval(this.intervalId);
        this.intervalId = null;
      }
    }
  }

  /**
   * Resume polling (e.g., when tab is visible again)
   */
  resume() {
    if (this.isPolling && this.isPaused) {
      this.isPaused = false;
      // Reset error count on resume
      this.errorCount = 0;
      this.currentInterval = this.baseInterval;
      this.poll();
      this.scheduleNextPoll();
    }
  }

  /**
   * Schedule the next poll with exponential backoff on errors
   */
  private scheduleNextPoll() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }

    this.intervalId = setInterval(() => {
      if (!this.isPaused) {
        this.poll();
      }
    }, this.currentInterval);
  }

  /**
   * Perform a single poll
   */
  private async poll() {
    if (!this.options || this.isPaused) return;

    const { projectUuid, onUpdate, onError, onMaxErrors } = this.options;

    try {
      const data = await fetchRecentSpans(
        projectUuid,
        this.lastTimestamp?.toISOString()
      );
      
      // Filter out duplicates
      const newSpans = data.spans.filter(span => {
        if (this.seenSpanIds.has(span.uuid)) {
          return false;
        }
        this.seenSpanIds.add(span.uuid);
        return true;
      });

      if (newSpans.length > 0) {
        onUpdate?.(newSpans);
      }

      // Update last timestamp for next poll
      this.lastTimestamp = new Date(data.timestamp);
      
      // Reset error count and interval on success
      if (this.errorCount > 0) {
        this.errorCount = 0;
        this.currentInterval = this.baseInterval;
        this.scheduleNextPoll();
      }
      
      // Clean up old span IDs to prevent memory leak (keep last 1000)
      if (this.seenSpanIds.size > 1000) {
        const idsArray = Array.from(this.seenSpanIds);
        this.seenSpanIds = new Set(idsArray.slice(-500));
      }
    } catch (error) {
      this.errorCount++;
      console.error(`Polling error (attempt ${this.errorCount}/${MAX_CONSECUTIVE_ERRORS}):`, error);
      
      onError?.(error as Error);

      if (this.errorCount >= MAX_CONSECUTIVE_ERRORS) {
        // Stop polling after too many errors
        this.stop();
        onMaxErrors?.();
      } else {
        // Exponential backoff
        this.currentInterval = Math.min(
          this.currentInterval * ERROR_BACKOFF_MULTIPLIER,
          MAX_BACKOFF_MS
        );
        this.scheduleNextPoll();
      }
    }
  }

  /**
   * Check if polling is currently active
   */
  isActive(): boolean {
    return this.isPolling;
  }

  /**
   * Check if polling is paused
   */
  isPausedState(): boolean {
    return this.isPaused;
  }
}

// Create instance - not a singleton, each component creates its own
export const createSpanPollingService = () => new SpanPollingService();

// For backward compatibility, export a default instance
export const spanPollingService = new SpanPollingService();