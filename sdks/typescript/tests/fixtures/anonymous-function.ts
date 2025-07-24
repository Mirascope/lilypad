import { trace } from '@lilypad/typescript-sdk';

// Anonymous function without name in options
trace(async (x: number) => x * 2, { versioning: 'automatic' });

// Named function with versioning null (should not be extracted)
export const notVersioned = trace((x: number) => x * 3, { versioning: null });

// Named function without options (should not be extracted)
export const noOptions = trace((x: number) => x * 4);
