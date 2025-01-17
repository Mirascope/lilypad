import { createFileRoute, redirect } from "@tanstack/react-router";
export const Route = createFileRoute("/")({
  beforeLoad: ({ context, location }) => {
    if (!context.auth.isAuthenticated) {
      throw redirect({
        to: "/auth/login",
        search: {
          redirect: location.href,
          deviceCode: "",
        },
      });
    } else {
      throw redirect({
        to: "/projects",
        search: { redirect: undefined, deviceCode: undefined },
      });
    }
  },
  component: () => <div />,
});
