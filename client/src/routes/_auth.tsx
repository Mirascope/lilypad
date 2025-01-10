import { AppSidebar } from "@/components/AppSidebar";
import SidebarSkeleton from "@/components/SidebarSkeleton";
import { SidebarProvider } from "@/components/ui/sidebar";
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";
import { Suspense } from "react";

export const Route = createFileRoute("/_auth")({
  beforeLoad: async ({ context }) => {
    if (!context.auth.isAuthenticated) {
      throw redirect({
        to: "/auth/login",
        search: {
          redirect: undefined,
          deviceCode: undefined,
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
          <Suspense fallback={<SidebarSkeleton />}>
            <AppSidebar />
          </Suspense>
          <main className='flex-1 overflow-y-auto overflow-x-hidden pt-4 bg-secondary/10 pb-1'>
            <Outlet />
          </main>
        </SidebarProvider>
      </div>
    </>
  );
}
