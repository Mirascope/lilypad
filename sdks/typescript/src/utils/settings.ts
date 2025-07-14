import type { LilypadConfig } from '../types';

export type LilypadSettings = LilypadConfig;

let currentSettings: LilypadConfig | null = null;

export function getSettings(): LilypadConfig | null {
  return currentSettings;
}

export function setSettings(settings: LilypadConfig | null): void {
  currentSettings = settings;
}

export function isConfigured(): boolean {
  return currentSettings !== null;
}

export function mergeSettings(overrides: Partial<LilypadConfig>): LilypadConfig {
  const current = getSettings();
  if (!current) {
    throw new Error('Cannot merge settings when not configured');
  }
  return {
    ...current,
    ...overrides,
    batchProcessorOptions: {
      ...current.batchProcessorOptions,
      ...overrides.batchProcessorOptions,
    },
  };
}
