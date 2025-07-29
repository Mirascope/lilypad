import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { MistralInstrumentation } from './mistral-otel-instrumentation';

describe('MistralInstrumentation', () => {
  let instrumentation: MistralInstrumentation;

  beforeEach(() => {
    instrumentation = new MistralInstrumentation();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('instrumentationName', () => {
    it('should return the correct instrumentation name', () => {
      expect(instrumentation.instrumentationName).toBe('@lilypad/instrumentation-mistral');
    });
  });

  describe('instrumentationVersion', () => {
    it('should return the correct instrumentation version', () => {
      expect(instrumentation.instrumentationVersion).toBe('0.1.0');
    });
  });

  describe('configuration', () => {
    it('should accept configuration options', () => {
      const requestHook = vi.fn();
      const responseHook = vi.fn();

      const instrumentationWithHooks = new MistralInstrumentation({
        requestHook,
        responseHook,
        enabled: true,
      });

      expect(instrumentationWithHooks).toBeDefined();
      expect(instrumentationWithHooks.instrumentationName).toBe('@lilypad/instrumentation-mistral');
    });
  });

  describe('module support', () => {
    it('should correctly identify supported modules', () => {
      expect(instrumentation.instrumentationName).toBe('@lilypad/instrumentation-mistral');
      expect(instrumentation.instrumentationVersion).toBe('0.1.0');
    });
  });
});
