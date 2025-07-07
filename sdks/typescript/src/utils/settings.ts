import type { LilypadConfig } from '../types';

let currentSettings: LilypadConfig | null = null;

export function getSettings(): LilypadConfig {
  if (!currentSettings) {
    throw new Error('Lilypad SDK not configured. Call configure() first.');
  }
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
  return {
    ...current,
    ...overrides,
    batchProcessorOptions: {
      ...current.batchProcessorOptions,
      ...overrides.batchProcessorOptions,
    },
  };
}
