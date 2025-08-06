import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { trace } from '@opentelemetry/api';
import {
  ConsoleSpanExporter,
  SimpleSpanProcessor,
} from '@opentelemetry/sdk-trace-base';
import { NodeTracerProvider } from '@opentelemetry/sdk-trace-node';
import { getTracer } from './configure';
import { CryptoIdGenerator } from './utils/id-generator';

vi.mock('@opentelemetry/sdk-trace-base', () => ({
  ConsoleSpanExporter: vi.fn().mockImplementation(() => ({})),
  SimpleSpanProcessor: vi.fn().mockImplementation(() => ({})),
}));

vi.mock('@opentelemetry/sdk-trace-node', () => ({
  NodeTracerProvider: vi.fn().mockImplementation(() => ({
    register: vi.fn(),
  })),
}));

vi.mock('./utils/id-generator', () => ({
  CryptoIdGenerator: vi.fn().mockImplementation(() => ({})),
}));

describe('configure', () => {
  let consoleErrorSpy: any;
  let consoleDebugSpy: any;
  let moduleState: any;

  beforeEach(async () => {
    vi.clearAllMocks();
    consoleErrorSpy = vi.spyOn(console, 'error').mockImplementation(() => {});
    consoleDebugSpy = vi.spyOn(console, 'debug').mockImplementation(() => {});
    vi.resetModules();
    moduleState = await import('./configure');
  });

  afterEach(() => {
    consoleErrorSpy.mockRestore();
    consoleDebugSpy.mockRestore();
  });

  it('should configure in debug mode', () => {
    const mockRegister = vi.fn();
    const MockNodeTracerProvider = vi.fn().mockImplementation(() => ({
      register: mockRegister,
    }));
    vi.mocked(NodeTracerProvider).mockImplementation(MockNodeTracerProvider);

    moduleState.configure({ mode: 'debug' });

    expect(consoleDebugSpy).toHaveBeenCalledWith(
      'Configuring lilypad SDK in debug mode.'
    );
    expect(ConsoleSpanExporter).toHaveBeenCalled();
    expect(SimpleSpanProcessor).toHaveBeenCalled();
    expect(CryptoIdGenerator).toHaveBeenCalled();
    expect(NodeTracerProvider).toHaveBeenCalledWith({
      idGenerator: expect.any(Object),
      spanProcessors: [expect.any(Object)],
    });
    expect(mockRegister).toHaveBeenCalled();
  });

  it('should not configure if no mode is provided', () => {
    moduleState.configure({});

    expect(ConsoleSpanExporter).not.toHaveBeenCalled();
    expect(SimpleSpanProcessor).not.toHaveBeenCalled();
    expect(NodeTracerProvider).not.toHaveBeenCalled();
  });

  it('should not configure without config', () => {
    moduleState.configure();

    expect(ConsoleSpanExporter).not.toHaveBeenCalled();
    expect(SimpleSpanProcessor).not.toHaveBeenCalled();
    expect(NodeTracerProvider).not.toHaveBeenCalled();
  });

  it('should throw error for invalid mode', () => {
    expect(() => moduleState.configure({ mode: 'invalid' as any })).toThrow(
      "Invalid mode: invalid. Must be 'debug' or undefined."
    );
  });

  it('should handle configuration errors', () => {
    const mockError = new Error('Configuration failed');
    vi.mocked(ConsoleSpanExporter).mockImplementationOnce(() => {
      throw mockError;
    });

    expect(() => moduleState.configure({ mode: 'debug' })).toThrow(
      'Failed to configure Lilypad SDK: Configuration failed'
    );
  });

  it('should handle non-Error configuration errors', () => {
    vi.mocked(ConsoleSpanExporter).mockImplementationOnce(() => {
      throw 'String error';
    });

    expect(() => moduleState.configure({ mode: 'debug' })).toThrow(
      'Failed to configure Lilypad SDK: String error'
    );
  });

  it('should not reconfigure if already configured', async () => {
    const mockRegister = vi.fn();
    const MockNodeTracerProvider = vi.fn().mockImplementation(() => ({
      register: mockRegister,
    }));
    vi.mocked(NodeTracerProvider).mockImplementation(MockNodeTracerProvider);

    const freshModule = await import('./configure');
    freshModule.configure({ mode: 'debug' });
    expect(mockRegister).toHaveBeenCalledTimes(1);

    freshModule.configure({ mode: 'debug' });
    expect(consoleErrorSpy).toHaveBeenCalledWith(
      'TracerProvider already initialized.'
    );
    expect(mockRegister).toHaveBeenCalledTimes(1);
  });
});

describe('getTracer', () => {
  it('should get tracer with default name', () => {
    const mockGetTracer = vi.fn().mockReturnValue({});
    trace.getTracer = mockGetTracer;

    getTracer();

    expect(mockGetTracer).toHaveBeenCalledWith('lilypad');
  });

  it('should get tracer with custom name', () => {
    const mockGetTracer = vi.fn().mockReturnValue({});
    trace.getTracer = mockGetTracer;

    getTracer('custom-name');

    expect(mockGetTracer).toHaveBeenCalledWith('custom-name');
  });
});
