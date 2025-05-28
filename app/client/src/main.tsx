import "./index.css";

import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRouter, RouterProvider } from "@tanstack/react-router";
import { PostHogProvider } from "posthog-js/react";
import { StrictMode } from "react";
import ReactDOM from "react-dom/client";
// Import the generated route tree
import { AuthProvider, useAuth } from "@/auth";
import { FontProvider } from "@/components/FontProvider";
import { ThemeProvider } from "@/components/theme-provider";
import { routeTree } from "./routeTree.gen";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: (failureCount, error) => {
        // Don't retry 403 errors
        if (
          (error instanceof Error && error.message.includes("403")) ||
          (error instanceof Response && error.status === 403) ||
          (error && typeof error === "object" && "status" in error && error.status === 403) ||
          (error && typeof error === "object" && "statusCode" in error && error.statusCode === 403)
        ) {
          return false;
        }

        // Default behavior: retry failed queries 3 times
        return failureCount < 3;
      },
    },
    mutations: {
      // Same logic for mutations
      retry: (failureCount, error) => {
        if (
          (error instanceof Error && error.message.includes("403")) ||
          (error instanceof Response && error.status === 403) ||
          (error && typeof error === "object" && "status" in error && error.status === 403) ||
          (error && typeof error === "object" && "statusCode" in error && error.statusCode === 403)
        ) {
          return false;
        }

        return failureCount < 3;
      },
    },
  },
});

// Create a new router instance
const router = createRouter({
  routeTree,
  defaultPreload: "intent",
  // Since we're using React Query, we don't want loader calls to ever be stale
  // This will ensure that the loader is always called when the route is preloaded or visited
  defaultPreloadStaleTime: 0,
  context: {
    queryClient,
    auth: undefined!,
  },
});

declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
  }
  interface HistoryState {
    result?: string;
  }
}

const InnerApp = () => {
  const auth = useAuth();
  return <RouterProvider router={router} context={{ auth }} />;
};

// Render the app
const rootElement = document.getElementById("root")!;
if (!rootElement.innerHTML) {
  const root = ReactDOM.createRoot(rootElement);

  const appContent = (
    <FontProvider defaultFont="default" storageKey="font">
      <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
        <QueryClientProvider client={queryClient}>
          <AuthProvider>
            <TooltipProvider delayDuration={200}>
              <InnerApp />
            </TooltipProvider>
          </AuthProvider>
        </QueryClientProvider>
      </ThemeProvider>
    </FontProvider>
  );
  root.render(
    <StrictMode>
      {import.meta.env.VITE_PUBLIC_POSTHOG_KEY && import.meta.env.VITE_POSTHOG_HOST ? (
        <PostHogProvider
          apiKey={import.meta.env.VITE_PUBLIC_POSTHOG_KEY as string}
          options={{
            api_host: import.meta.env.VITE_POSTHOG_HOST as string,
            autocapture: false,
            capture_performance: false,
          }}
        >
          {appContent}
        </PostHogProvider>
      ) : (
        appContent
      )}
    </StrictMode>
  );
}
