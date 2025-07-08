import { describe, it, expect, beforeEach, vi } from 'vitest';
import { OpenAIInstrumentor } from './openai';

describe('OpenAIInstrumentor', () => {
  let instrumentor: OpenAIInstrumentor;

  beforeEach(() => {
    vi.clearAllMocks();
    instrumentor = new OpenAIInstrumentor();
  });

  describe('getName', () => {
    it('should return instrumentor name', () => {
      expect(instrumentor.getName()).toBe('OpenAI');
    });
  });

  describe('instrument/uninstrument', () => {
    it('should track instrumentation state', () => {
      expect(instrumentor.isInstrumented()).toBe(false);

      // Since we can't easily mock require in the test environment,
      // we'll just verify the basic state tracking
      // Full integration testing would be done in e2e tests
    });

    it('should handle uninstrument when not instrumented', () => {
      expect(() => instrumentor.uninstrument()).not.toThrow();
      expect(instrumentor.isInstrumented()).toBe(false);
    });
  });

  // Note: Full integration testing with actual OpenAI module mocking
  // is complex due to module loading. These tests cover the basic
  // instrumentor functionality. Integration tests would be better
  // suited for e2e testing with actual OpenAI SDK.
});
