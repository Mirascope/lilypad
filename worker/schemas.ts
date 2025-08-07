import { z } from 'zod';

// Health endpoint schemas
export const HealthResponseSchema = z.object({
  status: z.literal('ok'),
  timestamp: z.string().datetime(),
  environment: z.string(),
});

export type HealthResponse = z.infer<typeof HealthResponseSchema>;

// Error response schemas (for consistent error handling)
export const ErrorResponseSchema = z.object({
  error: z.string(),
  message: z.string().optional(),
});

export type ErrorResponse = z.infer<typeof ErrorResponseSchema>;
