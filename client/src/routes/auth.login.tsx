import { createFileRoute, redirect } from "@tanstack/react-router";

import { GithubLogin } from "@/components/GithubLogin";
import { GoogleLogin } from "@/components/GoogleLogin";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";

interface LoginSearchParam {
  redirect?: string;
}

const fallback = "/projects";
export const Route = createFileRoute("/auth/login")({
  validateSearch: (search): LoginSearchParam => {
    return {
      redirect: (search.redirect as string) || undefined,
    };
  },
  beforeLoad: ({ context, search }) => {
    if (context.auth.isAuthenticated) {
      throw redirect({
        to: search.redirect ?? fallback,
      });
    }
  },
  component: () => <LoginComponent />,
});

const LoginComponent = () => {
  const { redirect } = Route.useSearch();

  return (
    <div className="flex items-center justify-center h-screen">
      <Card className="w-[600px] m-0">
        <CardHeader>
          <CardTitle>Welcome to Lilypad</CardTitle>
          <CardDescription>Sign in to continue</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <GithubLogin redirect={redirect} />
          <GoogleLogin redirect={redirect} />
        </CardContent>
        <CardFooter>
          <Typography variant="p" affects="muted">
            By signing in, you agree to our{" "}
            <a
              href="https://mirascope.com/terms/service"
              target="_blank"
              rel="noopener noreferrer"
            >
              Terms of Service
            </a>{" "}
            and{" "}
            <a
              href="https://mirascope.com/privacy"
              target="_blank"
              rel="noopener noreferrer"
            >
              Privacy Policy
            </a>
            .
          </Typography>
        </CardFooter>
      </Card>
    </div>
  );
};
