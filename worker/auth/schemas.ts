import { z } from '@hono/zod-openapi';

// /auth/logout responses
export const LogoutSuccessResponseSchema = z
  .object({
    success: z.literal(true),
    message: z.string(),
  })
  .openapi('LogoutSuccessResponse');

export const LogoutErrorResponseSchema = z
  .object({
    success: z.literal(false),
    error: z.string(),
  })
  .openapi('LogoutErrorResponse');

// /auth/me responses
export const MeSuccessResponseSchema = z
  .object({
    success: z.literal(true),
    user: z.object({
      id: z.string().uuid(),
      email: z.string().email(),
      name: z.string().nullable(),
    }),
  })
  .openapi('MeSuccessResponse');

export const MeErrorResponseSchema = z
  .object({
    success: z.literal(false),
    error: z.string(),
  })
  .openapi('MeErrorResponse');

// OAuth query parameters (for documentation only, not validation)
export const OAuthCallbackQuerySchema = z
  .object({
    code: z.string().optional(),
    state: z.string().optional(),
    error: z.string().optional(),
  })
  .openapi('OAuthCallbackQuery');
