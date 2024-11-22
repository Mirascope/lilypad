import { Outlet, createFileRoute, redirect } from "@tanstack/react-router";
import { SidebarProvider, SidebarTrigger } from "@/components/ui/sidebar";
import { AppSidebar } from "@/components/AppSidebar";

export const Route = createFileRoute("/_auth")({
  beforeLoad: ({ context, location }) => {
    if (
      !context.auth.isAuthenticated &&
      process.env.NODE_ENV !== "development"
    ) {
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
      <SidebarProvider>
        <AppSidebar />
        <main>
          <SidebarTrigger />
          <Outlet />
        </main>
      </SidebarProvider>
    </>
  );
}
