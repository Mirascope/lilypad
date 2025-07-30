import type { User } from '@/db/schema';
import type { Database } from '@/db/utils';
import type { Environment } from '@/worker/environment';

// Base variables with optional user for all routes
export type BaseVariables = {
  db: Database;
  user?: User; // Optional - populated by middleware when authenticated
};

// Base environment type
export type BaseEnv = {
  Bindings: Environment;
  Variables: BaseVariables;
};

// Deprecated - use BaseEnv instead
export type BaseAuthEnv = BaseEnv;
export type AuthenticatedEnv = BaseEnv;
