import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  Outlet,
  RouterProvider,
} from "@tanstack/react-router";
import { render, waitFor, RenderResult, screen } from "@testing-library/react";
import { expect, mock } from "bun:test";
import { act } from "react";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthContext, AuthProvider } from "./auth";

export const mockAuthContext: AuthContext = {
  isAuthenticated: false,
  user: null,
  logout: mock(() => undefined),
  setSession: mock(() => undefined),
  setProject: mock(() => undefined),
  activeProject: null,
  setEnvironment: mock(() => undefined),
  activeEnvironment: null,
  setTermsVersion: mock(() => undefined),
  setPrivacyPolicyVersion: mock(() => undefined),
  loadPrivacyPolicyVersion: () => "1.0.0",
  loadTermsVersion: () => "1.0.0",
  updateUserConfig: mock(() => undefined),
  userConfig: null,
};

export const mockAuthenticatedContext: AuthContext = {
  ...mockAuthContext,
  isAuthenticated: true,
  user: { 
    uuid: "1", 
    email: "test@example.com",
    access_token: "mock-token",
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
};

export interface RenderRouteOptions {
  path: string;
  component: React.ComponentType;
  validateSearch?: (search: Record<string, unknown>) => unknown;
  authContext?: AuthContext;
  initialPath?: string;
  search?: Record<string, string>;
  params?: Record<string, string>;
}

export const createTestQueryClient = () => new QueryClient({
  defaultOptions: {
    queries: { retry: false },
    mutations: { retry: false },
  },
});

export const renderRoute = async (options: RenderRouteOptions): Promise<RenderResult & { router: ReturnType<typeof createRouter> }> => {
  const { 
    path, 
    component: Component, 
    validateSearch, 
    authContext = mockAuthContext,
    initialPath,
    search = {},
    params = {} 
  } = options;

  const queryClient = createTestQueryClient();

  const rootRoute = createRootRoute({
    component: Outlet,
  });

  const testRoute = createRoute({
    getParentRoute: () => rootRoute,
    path,
    component: Component,
    validateSearch,
  });

  const routeTree = rootRoute.addChildren([testRoute]);

  // Build the path with params
  let finalPath = initialPath ?? path;
  
  // Replace params in the path
  Object.entries(params).forEach(([key, value]) => {
    finalPath = finalPath.replace(`$${key}`, value);
  });
  
  const memoryHistory = createMemoryHistory({
    initialEntries: [
      finalPath +
        (Object.keys(search).length ? `?${new URLSearchParams(search).toString()}` : ""),
    ],
  });

  const router = createRouter({
    routeTree,
    history: memoryHistory,
    context: {
      queryClient,
      auth: authContext,
    },
  });

  let result: RenderResult;

  await act(async () => {
    result = render(
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <RouterProvider router={router} />
        </AuthProvider>
      </QueryClientProvider>
    );
    
    await waitFor(() => {
      expect(router.state.status).toBe("idle");
    });
  });

  return { ...result!, router };
};

// Utility for testing components that require debug output
export const debugScreen = () => {
  console.log("Current DOM:");
  screen.debug();
};
