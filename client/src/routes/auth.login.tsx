import { redirect, createFileRoute, useNavigate } from "@tanstack/react-router";

import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { GithubLogin } from "@/components/GithubLogin";

const fallback = "/projects" as const;
export const Route = createFileRoute("/auth/login")({
  validateSearch: (search) => {
    return {
      redirect: (search.redirect as string) || undefined,
      deviceCode: search.deviceCode as string,
    };
  },
  beforeLoad: ({ context, search }) => {
    if (context.auth.isAuthenticated) {
      throw redirect({
        to: search.redirect || fallback,
        search: { deviceCode: search.deviceCode },
      });
    }
  },
  component: () => <LoginComponent />,
});

const LoginComponent = () => {
  const navigate = useNavigate();
  // const isLocal = import.meta.env.DEV;
  const isLocal = false;
  return (
    <div className='flex items-center justify-center h-screen'>
      <Card className='w-[600px] m-0'>
        <CardHeader>
          <CardTitle>Welcome to Lilypad</CardTitle>
          <CardDescription>
            {isLocal ? "Local environment" : "Sign in to continue"}
          </CardDescription>
        </CardHeader>
        <CardContent className='flex flex-col gap-2'>
          {isLocal ? (
            <Button onClick={() => navigate({ to: "/projects" })}>
              Sign in with Local
            </Button>
          ) : (
            <GithubLogin />
          )}
        </CardContent>
      </Card>
    </div>
  );
};
