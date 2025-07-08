import { describe, it, expect, beforeEach } from 'vitest';
import { getSettings, setSettings, isConfigured, mergeSettings } from './settings';
import type { LilypadConfig } from '../types';

describe('settings', () => {
  const validConfig: LilypadConfig = {
    apiKey: 'test-api-key',
    projectId: '123e4567-e89b-12d3-a456-426614174000',
    baseUrl: 'https://api.test.com',
    logLevel: 'info',
  };

  beforeEach(() => {
    // Reset settings before each test
    setSettings(null);
  });

  describe('setSettings', () => {
    it('should store settings', () => {
      setSettings(validConfig);
      expect(getSettings()).toEqual(validConfig);
    });

    it('should overwrite existing settings', () => {
      const firstConfig = { ...validConfig, logLevel: 'debug' as const };
      const secondConfig = { ...validConfig, logLevel: 'error' as const };

      setSettings(firstConfig);
      expect(getSettings()?.logLevel).toBe('debug');

      setSettings(secondConfig);
      expect(getSettings()?.logLevel).toBe('error');
    });

    it('should accept null to clear settings', () => {
      setSettings(validConfig);
      expect(getSettings()).not.toBeNull();

      setSettings(null);
      expect(getSettings()).toBeNull();
    });
  });

  describe('getSettings', () => {
    it('should return null when not configured', () => {
      expect(getSettings()).toBeNull();
    });

    it('should return stored settings', () => {
      setSettings(validConfig);
      const retrieved = getSettings();

      expect(retrieved).toEqual(validConfig);
      expect(retrieved).toBe(getSettings()); // Same reference
    });
  });

  describe('isConfigured', () => {
    it('should return false when settings are null', () => {
      expect(isConfigured()).toBe(false);
    });

    it('should return true when settings are present', () => {
      setSettings(validConfig);
      expect(isConfigured()).toBe(true);
    });

    it('should return false after clearing settings', () => {
      setSettings(validConfig);
      expect(isConfigured()).toBe(true);

      setSettings(null);
      expect(isConfigured()).toBe(false);
    });
  });

  describe('settings reference', () => {
    it('should store reference to settings object', () => {
      const config = { ...validConfig };
      setSettings(config);

      // Modifying the original config will affect settings
      // This is the current behavior - settings are not deep cloned
      config.apiKey = 'modified-key';

      // Settings will be changed because we store the reference
      expect(getSettings()?.apiKey).toBe('modified-key');
    });
  });

  describe('mergeSettings', () => {
    it('should throw error when not configured', () => {
      expect(() => mergeSettings({ apiKey: 'new-key' })).toThrow(
        'Cannot merge settings when not configured',
      );
    });

    it('should merge simple properties', () => {
      setSettings(validConfig);
      const merged = mergeSettings({ apiKey: 'new-api-key', logLevel: 'debug' });

      expect(merged).toEqual({
        ...validConfig,
        apiKey: 'new-api-key',
        logLevel: 'debug',
        batchProcessorOptions: {},
      });
    });

    it('should merge batchProcessorOptions', () => {
      const configWithBatch: LilypadConfig = {
        ...validConfig,
        batchProcessorOptions: {
          maxBatchSize: 100,
          scheduledDelayMillis: 1000,
        },
      };

      setSettings(configWithBatch);
      const merged = mergeSettings({
        batchProcessorOptions: {
          maxBatchSize: 200,
        },
      });

      expect(merged.batchProcessorOptions).toEqual({
        maxBatchSize: 200,
        scheduledDelayMillis: 1000,
      });
    });

    it('should handle merging with undefined batchProcessorOptions', () => {
      setSettings(validConfig);
      const merged = mergeSettings({
        apiKey: 'new-key',
        batchProcessorOptions: {
          maxBatchSize: 50,
        },
      });

      expect(merged.batchProcessorOptions).toEqual({
        maxBatchSize: 50,
      });
    });

    it('should not modify original settings', () => {
      setSettings(validConfig);
      const originalApiKey = validConfig.apiKey;

      mergeSettings({ apiKey: 'new-key' });

      expect(getSettings()?.apiKey).toBe(originalApiKey);
    });

    it('should return a new object', () => {
      setSettings(validConfig);
      const merged = mergeSettings({});

      expect(merged).not.toBe(getSettings());
      expect(merged).toEqual({
        ...getSettings(),
        batchProcessorOptions: {},
      });
    });
  });
});
