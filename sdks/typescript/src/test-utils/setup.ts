import { vi, beforeEach } from 'vitest';

// Mock console methods to avoid noise in tests
global.console = {
  ...console,
  log: vi.fn(),
  info: vi.fn(),
  warn: vi.fn(),
  error: vi.fn(),
  debug: vi.fn(),
};

// Reset mocks before each test
beforeEach(() => {
  vi.clearAllMocks();
});
