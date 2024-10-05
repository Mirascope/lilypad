import { Button } from "@/components/ui/button";
import { createRootRoute, Link, Outlet } from "@tanstack/react-router";
import { TanStackRouterDevtools } from "@tanstack/router-devtools";

export const Route = createRootRoute({
  component: () => (
    <>
      <div className='p-2 flex gap-2'>
        <Button variant='link' asChild>
          <Link to='/' className='[&.active]:font-bold'>
            Home
          </Link>
        </Button>
        <Button variant='link' asChild>
          <Link to='/editor' className='[&.active]:font-bold'>
            Prompt Editor
          </Link>
        </Button>
        <Button variant='link' asChild>
          <Link to='/traces' className='[&.active]:font-bold'>
            Calls
          </Link>
        </Button>
        <Button variant='link' asChild>
          <Link to='/diff' className='[&.active]:font-bold'>
            Diff
          </Link>
        </Button>
      </div>
      <hr />
      <Outlet />
      <TanStackRouterDevtools />
    </>
  ),
});
