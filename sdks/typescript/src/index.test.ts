import { describe, it, expect } from 'vitest';
import lilypad, {
  configure,
  getTracerProvider,
  getTracer,
  shutdown,
  logger,
  type LilypadConfig,
  type LogLevel,
} from './index';

describe('index', () => {
  describe('named exports', () => {
    it('should export configure function', () => {
      expect(configure).toBeDefined();
      expect(typeof configure).toBe('function');
    });

    it('should export getTracerProvider function', () => {
      expect(getTracerProvider).toBeDefined();
      expect(typeof getTracerProvider).toBe('function');
    });

    it('should export getTracer function', () => {
      expect(getTracer).toBeDefined();
      expect(typeof getTracer).toBe('function');
    });

    it('should export shutdown function', () => {
      expect(shutdown).toBeDefined();
      expect(typeof shutdown).toBe('function');
    });

    it('should export logger object', () => {
      expect(logger).toBeDefined();
      expect(typeof logger).toBe('object');
      expect(logger.info).toBeDefined();
      expect(logger.error).toBeDefined();
      expect(logger.warn).toBeDefined();
      expect(logger.debug).toBeDefined();
    });

    it('should export types', () => {
      // Type exports are compile-time only, but we can verify they're available
      const config: LilypadConfig = {
        apiKey: 'test',
        projectId: '123e4567-e89b-12d3-a456-426614174000',
      };
      const level: LogLevel = 'info';
      expect(config).toBeDefined();
      expect(level).toBeDefined();
    });
  });

  describe('default export', () => {
    it('should export lilypad object with all methods', () => {
      expect(lilypad).toBeDefined();
      expect(lilypad.configure).toBe(configure);
      expect(lilypad.shutdown).toBe(shutdown);
      expect(lilypad.getTracer).toBe(getTracer);
      expect(lilypad.logger).toBe(logger);
    });

    it('should have correct shape', () => {
      expect(Object.keys(lilypad).sort()).toEqual(
        ['configure', 'getTracer', 'logger', 'shutdown'].sort(),
      );
    });
  });
});
