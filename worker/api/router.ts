import { Hono } from 'hono';

import type { Environment } from '@/worker/environment';

export const apiRouter = new Hono<{
  Bindings: Environment;
}>();
