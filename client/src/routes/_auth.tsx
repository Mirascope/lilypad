import { useAuth } from "@/auth";
import { AppSidebar } from "@/components/AppSidebar";
import { LayoutSkeleton } from "@/components/LayoutSkeleton";
import SidebarSkeleton from "@/components/SidebarSkeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { SidebarProvider } from "@/components/ui/sidebar";
import { licenseQueryOptions } from "@/ee/utils/organizations";
import { diffDays } from "@/utils/dates";
import { fetchUsersByOrganization } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";
import { AlertTriangle } from "lucide-react";
import { usePostHog } from "posthog-js/react";
import { Suspense, useEffect, useState } from "react";

export const Route = createFileRoute("/_auth")({
  beforeLoad: ({ context }) => {
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
  loader: async ({ context: { queryClient } }) => {
    await queryClient.prefetchQuery({
      queryKey: ["usersByOrganization"],
      queryFn: () => fetchUsersByOrganization(),
    });
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
  const { data: licenseInfo } = useSuspenseQuery(licenseQueryOptions());
  const [showAlert, setShowAlert] = useState(true);

  const daysLeft = diffDays(new Date(licenseInfo.expires_at));

  useEffect(() => {
    if (user && posthog && !posthog.get_distinct_id()?.includes(user.email)) {
      posthog.identify(user.email, {
        email: user.email,
      });
    }
  }, [posthog, user?.uuid, user?.email]);
  return (
    <div className='flex flex-col border-collapse overflow-hidden'>
      <SidebarProvider>
        <Suspense fallback={<SidebarSkeleton />}>
          <AppSidebar />
        </Suspense>
        <main className='flex-1 overflow-hidden bg-secondary/10'>
          {daysLeft < 14 && showAlert && (
            <Alert variant='warning' onClose={() => setShowAlert(false)}>
              <AlertTriangle className='h-4 w-4' />
              <AlertTitle>Warning</AlertTitle>
              <AlertDescription>{`Your license will expire in ${daysLeft} days.`}</AlertDescription>
            </Alert>
          )}
          <Outlet />
        </main>
      </SidebarProvider>
    </div>
  );
}
