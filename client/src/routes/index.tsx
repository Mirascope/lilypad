import { redirect } from "@tanstack/react-router";
import { createFileRoute } from "@tanstack/react-router";
export const Route = createFileRoute("/")({
  beforeLoad: ({ context, location }) => {
    if (!context.auth.isAuthenticated && !import.meta.env.DEV) {
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
