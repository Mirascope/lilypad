import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";
import { SidebarProvider } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";

export const Route = createFileRoute("/_auth")({
  beforeLoad: ({ context, location }) => {
    if (!context.auth.isAuthenticated && !import.meta.env.DEV) {
      throw redirect({
        to: "/auth/login",
        search: {
          redirect: location.href,
          deviceCode: "",
        },
      });
    }
  },
  component: AuthLayout,
});

function AuthLayout() {
  return (
    <>
      <div className='flex h-screen border-collapse overflow-hidden'>
        <SidebarProvider>
          <AppSidebar />
          <main className='flex-1 overflow-y-auto overflow-x-hidden pt-4 bg-secondary/10 pb-1'>
            <Outlet />
          </main>
        </SidebarProvider>
      </div>
    </>
  );
}
