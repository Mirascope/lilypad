import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import { Logger } from './logger';

describe('Logger', () => {
  let logger: Logger;
  let consoleLogSpy: any;
  let consoleInfoSpy: any;
  let consoleWarnSpy: any;
  let consoleErrorSpy: any;
  let consoleDebugSpy: any;

  beforeEach(() => {
    logger = new Logger();
    consoleLogSpy = vi.spyOn(console, 'log').mockImplementation(() => {});
    consoleInfoSpy = vi.spyOn(console, 'info').mockImplementation(() => {});
    consoleWarnSpy = vi.spyOn(console, 'warn').mockImplementation(() => {});
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    consoleDebugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('log levels', () => {
    it('should log all levels when set to debug', () => {
      logger.setLevel('debug');

      logger.debug('debug message');
      logger.info('info message');
      logger.warn('warn message');
      logger.error('error message');

      expect(consoleDebugSpy).toHaveBeenCalledWith('[Lilypad]', 'debug message');
      expect(consoleInfoSpy).toHaveBeenCalledWith('[Lilypad]', 'info message');
      expect(consoleWarnSpy).toHaveBeenCalledWith('[Lilypad]', 'warn message');
      expect(consoleErrorSpy).toHaveBeenCalledWith('[Lilypad]', 'error message');
    });

    it('should not log debug when set to info', () => {
      logger.setLevel('info');

      logger.debug('debug message');
      logger.info('info message');
      logger.warn('warn message');
      logger.error('error message');

      expect(consoleDebugSpy).not.toHaveBeenCalled();
      expect(consoleInfoSpy).toHaveBeenCalled();
      expect(consoleWarnSpy).toHaveBeenCalled();
      expect(consoleErrorSpy).toHaveBeenCalled();
    });

    it('should only log warn and error when set to warn', () => {
      logger.setLevel('warn');

      logger.debug('debug message');
      logger.info('info message');
      logger.warn('warn message');
      logger.error('error message');

      expect(consoleDebugSpy).not.toHaveBeenCalled();
      expect(consoleInfoSpy).not.toHaveBeenCalled();
      expect(consoleWarnSpy).toHaveBeenCalled();
      expect(consoleErrorSpy).toHaveBeenCalled();
    });

    it('should only log error when set to error', () => {
      logger.setLevel('error');

      logger.debug('debug message');
      logger.info('info message');
      logger.warn('warn message');
      logger.error('error message');

      expect(consoleDebugSpy).not.toHaveBeenCalled();
      expect(consoleInfoSpy).not.toHaveBeenCalled();
      expect(consoleWarnSpy).not.toHaveBeenCalled();
      expect(consoleErrorSpy).toHaveBeenCalled();
    });

    it('should log nothing when set to none', () => {
      logger.setLevel('none');

      logger.debug('debug message');
      logger.info('info message');
      logger.warn('warn message');
      logger.error('error message');

      expect(consoleDebugSpy).not.toHaveBeenCalled();
      expect(consoleInfoSpy).not.toHaveBeenCalled();
      expect(consoleWarnSpy).not.toHaveBeenCalled();
      expect(consoleErrorSpy).not.toHaveBeenCalled();
    });
  });

  describe('log method', () => {
    it('should use console.log for generic log', () => {
      logger.setLevel('info');
      logger.log('generic message');

      expect(consoleLogSpy).toHaveBeenCalledWith('[Lilypad] [LOG]', 'generic message');
    });

    it('should not log generic messages when level is warn or higher', () => {
      logger.setLevel('warn');
      logger.log('generic message');

      expect(consoleLogSpy).not.toHaveBeenCalled();
    });
  });

  describe('multiple arguments', () => {
    it('should pass all arguments to console methods', () => {
      logger.setLevel('debug');
      const obj = { key: 'value' };
      const arr = [1, 2, 3];

      logger.info('message', obj, arr);

      expect(consoleInfoSpy).toHaveBeenCalledWith('[Lilypad]', 'message', obj, arr);
    });
  });

  describe('default level', () => {
    it('should default to info level', () => {
      const defaultLogger = new Logger();

      defaultLogger.debug('debug');
      defaultLogger.info('info');

      expect(consoleDebugSpy).not.toHaveBeenCalled();
      expect(consoleInfoSpy).toHaveBeenCalled();
    });
  });
});
