import { AppSidebar } from "@/components/AppSidebar";
import { LayoutSkeleton } from "@/components/LayoutSkeleton";
import { Onboarding } from "@/components/Onboarding";
import SidebarSkeleton from "@/components/SidebarSkeleton";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Dialog, DialogContent, DialogTitle } from "@/components/ui/dialog";
import { SidebarProvider } from "@/components/ui/sidebar";
import { licenseQueryOptions } from "@/ee/utils/organizations";
import { diffDays } from "@/utils/dates";
import { fetchUsersByOrganization, userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";
import { AlertTriangle } from "lucide-react";
import { usePostHog } from "posthog-js/react";
import { Suspense, useEffect, useState } from "react";
import { toast } from "sonner";

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
  loader: ({ context: { queryClient } }) => {
    queryClient
      .prefetchQuery({
        queryKey: ["usersByOrganization"],
        queryFn: () => fetchUsersByOrganization(),
      })
      .catch(() => toast.error("Failed to fetch users"));
  },
  component: () => (
    <Suspense fallback={<LayoutSkeleton />}>
      <AuthLayout />
    </Suspense>
  ),
});

function AuthLayout() {
  const posthog = usePostHog();
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const { data: licenseInfo } = useSuspenseQuery(licenseQueryOptions());
  const [showAlert, setShowAlert] = useState<boolean>(true);
  const [onboardingOpen, setOnboardingOpen] = useState<boolean>(true);
  const daysLeft = diffDays(new Date(licenseInfo.expires_at));

  useEffect(() => {
    if (user && posthog && !posthog.get_distinct_id()?.includes(user.email)) {
      posthog.identify(user.email, {
        email: user.email,
      });
    }
  }, [posthog, user?.uuid, user?.email]);

  return (
    <div className="flex border-collapse flex-col overflow-hidden" data-product="lilypad">
      <SidebarProvider defaultOpen={false}>
        <Suspense fallback={<SidebarSkeleton />}>
          <AppSidebar />
        </Suspense>
        <main className="flex-1 overflow-hidden">
          {daysLeft < 14 && showAlert && (
            <Alert variant="warning" onClose={() => setShowAlert(false)}>
              <AlertTriangle className="h-4 w-4" />
              <AlertTitle>Warning</AlertTitle>
              <AlertDescription>{`Your license will expire in ${daysLeft} days.`}</AlertDescription>
            </Alert>
          )}
          {!user?.user_organizations?.length && (
            <Dialog open={onboardingOpen} onOpenChange={setOnboardingOpen}>
              <DialogTitle className="sr-only">Welcome</DialogTitle>
              <DialogContent className="h-[90vh] max-w-[90%] overflow-hidden">
                <Onboarding />
              </DialogContent>
            </Dialog>
          )}
          <Outlet />
        </main>
      </SidebarProvider>
    </div>
  );
}
