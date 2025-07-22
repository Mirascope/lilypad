/**
 * LilypadClient connection pooling for better performance
 */

import { LilypadClient } from '../../lilypad/generated/Client';
import type { LilypadConfig } from '../types';
import { BASE_URL } from '../constants';

class ClientPool {
  private clients = new Map<string, LilypadClient>();

  private getKey(settings: LilypadConfig): string {
    return `${settings.apiKey}:${settings.baseUrl || BASE_URL}`;
  }

  get(settings: LilypadConfig): LilypadClient {
    const key = this.getKey(settings);
    let client = this.clients.get(key);

    if (!client) {
      client = new LilypadClient({
        environment: () => settings.baseUrl || BASE_URL,
        apiKey: () => settings.apiKey,
      });
      this.clients.set(key, client);
    }

    return client;
  }

  clear(): void {
    this.clients.clear();
  }
}

// Singleton instance
const clientPool = new ClientPool();

/**
 * Get a pooled LilypadClient instance
 */
export function getPooledClient(settings: LilypadConfig): LilypadClient {
  return clientPool.get(settings);
}

/**
 * Clear all pooled clients
 */
export function clearClientPool(): void {
  clientPool.clear();
}
