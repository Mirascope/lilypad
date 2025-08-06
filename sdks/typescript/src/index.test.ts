import { describe, it, expect } from 'vitest';
import lilypad, { configure, instrument_openai } from './index';
import type { LilypadConfig } from './index';

describe('index exports', () => {
  it('should export default lilypad object', () => {
    expect(lilypad).toBeDefined();
    expect(lilypad.configure).toBeDefined();
    expect(lilypad.instrument_openai).toBeDefined();
    expect(typeof lilypad.configure).toBe('function');
    expect(typeof lilypad.instrument_openai).toBe('function');
  });

  it('should export named functions', () => {
    expect(configure).toBeDefined();
    expect(instrument_openai).toBeDefined();
    expect(typeof configure).toBe('function');
    expect(typeof instrument_openai).toBe('function');
  });

  it('should export the same functions in default and named exports', () => {
    expect(lilypad.configure).toBe(configure);
    expect(lilypad.instrument_openai).toBe(instrument_openai);
  });

  it('should export LilypadConfig type', () => {
    const config: LilypadConfig = { mode: 'debug' };
    expect(config).toBeDefined();
  });
});
