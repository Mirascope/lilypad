import { describe, it, expect, beforeEach, vi, afterEach } from 'vitest';
import { OpenAIInstrumentor } from './openai';

// Mock logger
vi.mock('../utils/logger', () => ({
  logger: {
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
    debug: vi.fn(),
  },
}));

// Mock settings
vi.mock('../utils/settings', () => ({
  getSettings: vi.fn(() => ({
    projectId: 'test-project-id',
  })),
}));

describe('OpenAIInstrumentor', () => {
  let instrumentor: OpenAIInstrumentor;

  beforeEach(() => {
    vi.clearAllMocks();
    instrumentor = new OpenAIInstrumentor();
  });

  afterEach(() => {
    vi.resetModules();
  });

  describe('getName', () => {
    it('should return instrumentor name', () => {
      expect(instrumentor.getName()).toBe('OpenAI');
    });
  });

  describe('instrument/uninstrument', () => {
    it('should track instrumentation state', () => {
      expect(instrumentor.isInstrumented()).toBe(false);
    });

    it('should handle uninstrument when not instrumented', () => {
      expect(() => instrumentor.uninstrument()).not.toThrow();
      expect(instrumentor.isInstrumented()).toBe(false);
    });

    it('should start as not instrumented', () => {
      // Just verify the initial state
      expect(instrumentor.isInstrumented()).toBe(false);
    });

    it('should warn when already instrumented', async () => {
      // Mock the instrumented flag to test the warning
      (instrumentor as any).isInstrumentedFlag = true;
      const { logger } = await import('../utils/logger');

      instrumentor.instrument();

      expect(logger.warn).toHaveBeenCalledWith('OpenAI already instrumented');
    });
  });
});
