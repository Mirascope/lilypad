import type { LogLevel } from '../types';

const LOG_LEVELS: Record<LogLevel | 'none', number> = {
  debug: 0,
  info: 1,
  warn: 2,
  error: 3,
  none: 999,
};

export class Logger {
  private logLevel: LogLevel | 'none' = 'info';
  private prefix = '[Lilypad]';

  setLevel(level: LogLevel | 'none'): void {
    this.logLevel = level;
  }

  private shouldLog(level: LogLevel | 'none'): boolean {
    if (this.logLevel === 'none') return false;
    return LOG_LEVELS[level] >= LOG_LEVELS[this.logLevel];
  }

  debug(...args: unknown[]): void {
    if (this.shouldLog('debug')) {
      console.debug(this.prefix, ...args);
    }
  }

  info(...args: unknown[]): void {
    if (this.shouldLog('info')) {
      console.info(this.prefix, ...args);
    }
  }

  warn(...args: unknown[]): void {
    if (this.shouldLog('warn')) {
      console.warn(this.prefix, ...args);
    }
  }

  error(...args: unknown[]): void {
    if (this.shouldLog('error')) {
      console.error(this.prefix, ...args);
    }
  }

  log(...args: unknown[]): void {
    if (this.shouldLog('info')) {
      console.log('[Lilypad] [LOG]', ...args);
    }
  }
}

export const logger = new Logger();

// Function to set global log level
export function setGlobalLogLevel(level: LogLevel | 'none'): void {
  logger.setLevel(level);
}
