import { createFileRoute, redirect } from "@tanstack/react-router";
export const Route = createFileRoute("/")({
  beforeLoad: ({ context }) => {
    if (!context.auth.isAuthenticated) {
      throw redirect({
        to: "/auth/login",
      });
    } else {
      throw redirect({
        to: "/projects",
      });
    }
  },
  component: () => <div />,
});
