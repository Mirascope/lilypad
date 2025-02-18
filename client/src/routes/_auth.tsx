import { useAuth } from "@/auth";
import { AppSidebar } from "@/components/AppSidebar";
import { LayoutSkeleton } from "@/components/LayoutSkeleton";
import SidebarSkeleton from "@/components/SidebarSkeleton";
import { SidebarProvider } from "@/components/ui/sidebar";
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";
import { usePostHog } from "posthog-js/react";
import { Suspense, useEffect } from "react";

export const Route = createFileRoute("/_auth")({
  beforeLoad: async ({ context }) => {
    if (!context.auth.isAuthenticated) {
      const currentPath = window.location.pathname + window.location.search;
      throw redirect({
        to: "/auth/login",
        search: {
          redirect: currentPath,
        },
      });
    }
  },
  component: () => (
    <Suspense fallback={<LayoutSkeleton />}>
      <AuthLayout />
    </Suspense>
  ),
});

function AuthLayout() {
  const posthog = usePostHog();
  const { user } = useAuth();

  useEffect(() => {
    if (user && posthog && !posthog.get_distinct_id()?.includes(user.email)) {
      posthog.identify(user.email, {
        email: user.email,
      });
    }
  }, [posthog, user?.uuid, user?.email]);
  return (
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
  );
}
