import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";

import { useAuth } from "@/auth";
import { GithubLogin } from "@/components/GithubLogin";
import { GoogleLogin } from "@/components/GoogleLogin";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { settingsQueryOptions } from "@/utils/settings";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";

type LoginSearchParam = {
  redirect?: string;
};

const fallback = "/projects" as const;
export const Route = createFileRoute("/auth/login")({
  validateSearch: (search): LoginSearchParam => {
    return {
      redirect: (search.redirect as string) || undefined,
    };
  },
  beforeLoad: ({ context, search }) => {
    if (context.auth.isAuthenticated) {
      throw redirect({
        to: search.redirect || fallback,
      });
    }
  },
  component: () => <LoginComponent />,
});

const LoginComponent = () => {
  const { redirect } = Route.useSearch();
  const { data: settings } = useSuspenseQuery(settingsQueryOptions());
  const isLocal = settings.environment === "local";

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
            <LocalLogin />
          ) : (
            <>
              <GithubLogin redirect={redirect} />
              <GoogleLogin redirect={redirect} />
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

const LocalLogin = () => {
  const { data } = useSuspenseQuery(userQueryOptions());
  const { setSession } = useAuth();
  const navigate = useNavigate();
  const handleLocalLogin = () => {
    setSession(data);
    navigate({
      to: "/projects",
    });
  };
  return <Button onClick={handleLocalLogin}>Sign in with Local</Button>;
};
