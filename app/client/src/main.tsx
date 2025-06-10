import "./index.css";

import { TooltipProvider } from "@/src/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRouter, RouterProvider } from "@tanstack/react-router";
import { PostHogProvider } from "posthog-js/react";
import { StrictMode } from "react";
import ReactDOM from "react-dom/client";
// Import the generated route tree
import { AuthProvider, useAuth } from "@/src/auth";
import { FontProvider } from "@/src/components/FontProvider";
import { ThemeProvider } from "@/src/components/theme-provider";
import { routeTree } from "./routeTree.gen";

const createRetryHandler = (nonRetryableStatusCodes: number[] = [403, 409]) => {
  return (failureCount: number, error: Error) => {
    const getStatusCode = (error: Error): number | null => {
      if (!error || typeof error !== "object") return null;
      // Check common status properties
      if ("status" in error) return error.status as number;
      if ("statusCode" in error) return error.statusCode as number;

      if (error instanceof Error && error.message) {
        const statusPattern = new RegExp(`\\b(${nonRetryableStatusCodes.join("|")})\\b`);
        const match = error.message.match(statusPattern);
        return match ? parseInt(match[1]) : null;
      }

      return null;
    };

    const statusCode = getStatusCode(error);
    const isNonRetryableError = statusCode !== null && nonRetryableStatusCodes.includes(statusCode);

    // Don't retry on non-retryable errors
    if (isNonRetryableError) {
      return false;
    }

    // Default behavior: retry failed requests up to 3 times
    return failureCount < 3;
  };
};

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: createRetryHandler([403, 409]),
    },
    mutations: {
      retry: createRetryHandler([403, 409]),
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
