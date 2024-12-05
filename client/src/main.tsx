import "./index.css";

import { StrictMode } from "react";
import ReactDOM from "react-dom/client";

import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { createRouter, RouterProvider } from "@tanstack/react-router";
// Import the generated route tree
import { routeTree } from "./routeTree.gen";
import { AuthProvider, useAuth } from "@/auth";

const queryClient = new QueryClient();

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

// Register the router instance for type safety
declare module "@tanstack/react-router" {
  interface Register {
    router: typeof router;
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
  root.render(
    <StrictMode>
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <TooltipProvider delayDuration={200}>
            <InnerApp />
          </TooltipProvider>
        </AuthProvider>
      </QueryClientProvider>
    </StrictMode>
  );
}
