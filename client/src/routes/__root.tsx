import { createRootRouteWithContext, Outlet } from "@tanstack/react-router";
import type { QueryClient } from "@tanstack/react-query";
import { lazy } from "react";
import { DefaultCatchBoundary } from "@/components/DefaultCatchBoundary";
import { NotFound } from "@/components/NotFound";
import { AuthContext } from "@/auth";
import { Toaster } from "@/components/ui/toaster";
const TanStackRouterDevtools =
  process.env.NODE_ENV === "production"
    ? () => null // Render nothing in production
    : lazy(() =>
        // Lazy load in development
        import("@tanstack/router-devtools").then((res) => ({
          default: res.TanStackRouterDevtools,
          // For Embedded Mode
          // default: res.TanStackRouterDevtoolsPanel
        }))
      );

const RootComponent = () => {
  return (
    <>
      <Outlet />
      <Toaster />
      <TanStackRouterDevtools position='bottom-right' />
    </>
  );
};

export const Route = createRootRouteWithContext<{
  queryClient: QueryClient;
  auth: AuthContext;
}>()({
  errorComponent: (props) => {
    return <DefaultCatchBoundary {...props} />;
  },
  notFoundComponent: () => <NotFound />,
  component: RootComponent,
});
