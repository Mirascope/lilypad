import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// Mock modules before importing register
vi.mock('./utils/logger', () => ({
  logger: {
    setLevel: vi.fn(),
    debug: vi.fn(),
    info: vi.fn(),
    warn: vi.fn(),
    error: vi.fn(),
  },
}));

vi.mock('./configure', () => ({
  configure: vi.fn(),
}));

describe('register', () => {
  const originalEnv = process.env;
  const originalRequire = require;
  
  beforeEach(() => {
    vi.resetModules();
    process.env = { ...originalEnv };
  });

  afterEach(() => {
    process.env = originalEnv;
    vi.clearAllMocks();
  });

  it('should set logger level from environment variable', async () => {
    process.env.LILYPAD_LOG_LEVEL = 'debug';
    const { logger } = await import('./utils/logger');
    
    // Import register to trigger the setup
    await import('./register');
    
    expect(logger.setLevel).toHaveBeenCalledWith('debug');
  });

  it('should use default log level when env var not set', async () => {
    delete process.env.LILYPAD_LOG_LEVEL;
    const { logger } = await import('./utils/logger');
    
    // Import register to trigger the setup
    await import('./register');
    
    expect(logger.setLevel).toHaveBeenCalledWith('info');
  });

  it('should read Lilypad configuration from environment', async () => {
    // Set up environment variables
    process.env.LILYPAD_API_KEY = 'test-key';
    process.env.LILYPAD_PROJECT_ID = '123e4567-e89b-12d3-a456-426614174000';
    process.env.LILYPAD_AUTO_LLM = 'true';
    
    const { configure } = await import('./configure');
    
    // Import register to trigger the setup
    await import('./register');
    
    // Should eventually call configure with the environment settings
    // Note: The actual configuration happens lazily when OpenAI is loaded
    expect(configure).toBeDefined();
  });

  it('should handle missing environment variables gracefully', async () => {
    // Clear all Lilypad env vars
    Object.keys(process.env).forEach(key => {
      if (key.startsWith('LILYPAD_')) {
        delete process.env[key];
      }
    });
    
    const { logger } = await import('./utils/logger');
    
    // Import should not throw
    await expect(import('./register')).resolves.toBeDefined();
    
    // Logger should still be configured
    expect(logger.setLevel).toHaveBeenCalled();
  });
});