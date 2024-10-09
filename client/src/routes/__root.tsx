import { Button } from "@/components/ui/button";
import { createRootRoute, Link, Outlet } from "@tanstack/react-router";
import { lazy } from "react";
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
export const Route = createRootRoute({
  component: () => (
    <>
      <div className='p-2 flex gap-2'>
        <Button variant='link' asChild>
          <Link to='/' className='[&.active]:font-bold'>
            Projects
          </Link>
        </Button>
      </div>
      <hr />
      <Outlet />
      <TanStackRouterDevtools />
    </>
  ),
});
