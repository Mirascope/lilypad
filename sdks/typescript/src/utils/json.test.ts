import { describe, it, expect } from 'vitest';
import { safeStringify } from './json';

describe('safeStringify', () => {
  it('should stringify simple objects', () => {
    const obj = { name: 'test', value: 42 };
    expect(safeStringify(obj)).toBe('{"name":"test","value":42}');
  });

  it('should handle null and undefined', () => {
    expect(safeStringify(null)).toBe('null');
    expect(safeStringify(undefined)).toBe('"[undefined]"');
  });

  it('should handle circular references', () => {
    const obj: any = { name: 'test' };
    obj.self = obj;
    expect(safeStringify(obj)).toBe('{"name":"test","self":"[Circular]"}');
  });

  it('should handle functions', () => {
    const obj = { fn: () => 'test' };
    expect(safeStringify(obj)).toBe('{"fn":"[Function]"}');
  });

  it('should handle arrays', () => {
    const arr = [1, 2, 3];
    expect(safeStringify(arr)).toBe('[1,2,3]');
  });

  it('should handle nested objects', () => {
    const obj = {
      level1: {
        level2: {
          value: 'deep',
        },
      },
    };
    expect(safeStringify(obj)).toBe('{"level1":{"level2":{"value":"deep"}}}');
  });

  it('should truncate long strings', () => {
    const longString = 'a'.repeat(11000);
    const result = safeStringify(longString, 100);
    expect(result).toHaveLength(100 + '... [truncated]'.length);
    expect(result).toContain('... [truncated]');
  });

  it('should handle objects that throw during serialization', () => {
    const obj = {
      get bad() {
        throw new Error('Serialization error');
      },
    };
    expect(safeStringify(obj)).toBe('[Unable to stringify]');
  });

  it('should handle complex nested structures with circular references', () => {
    const parent: any = { name: 'parent' };
    const child: any = { name: 'child', parent };
    parent.child = child;

    const result = safeStringify(parent);
    expect(result).toContain('"name":"parent"');
    expect(result).toContain('"name":"child"');
    expect(result).toContain('[Circular]');
  });

  it('should respect maxLength parameter', () => {
    const obj = { data: 'test'.repeat(100) };
    const result = safeStringify(obj, 50);
    expect(result.length).toBeLessThanOrEqual(50 + '... [truncated]'.length);
  });
});
