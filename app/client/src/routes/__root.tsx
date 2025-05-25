import { AuthContext } from "@/auth";
import { DefaultCatchBoundary } from "@/components/DefaultCatchBoundary";
import { useFont } from "@/components/FontProvider";
import { NotFound } from "@/components/NotFound";
import { Toaster } from "@/components/ui/sonner";

import type { QueryClient } from "@tanstack/react-query";
import { createRootRouteWithContext, Outlet } from "@tanstack/react-router";
import { lazy } from "react";
const TanStackRouterDevtools =
  process.env.NODE_ENV === "production"
    ? () => null // Render nothing in production
    : lazy(() =>
        // Lazy load in development
        import("@tanstack/react-router-devtools").then((res) => ({
          default: res.TanStackRouterDevtools,
          // For Embedded Mode
          // default: res.TanStackRouterDevtoolsPanel
        }))
      );

const RootComponent = () => {
  const { font } = useFont();
  return (
    <>
      <Outlet />
      <Toaster
        richColors
        toastOptions={{
          className: font === "fun" ? "fun" : "professional",
        }}
      />
      <TanStackRouterDevtools position="bottom-right" />
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
