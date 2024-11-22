import {
  redirect,
  createFileRoute,
  useRouter,
  useNavigate,
} from "@tanstack/react-router";

import { useAuth } from "@/auth";
import { LoginType } from "@/types/types";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { GithubButton } from "@/components/GithubButton";
import { GoogleButton } from "@/components/GoogleButton";
import { Button } from "@/components/ui/button";

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
      });
    }
  },
  component: () => <LoginComponent />,
});

const LoginComponent = () => {
  const auth = useAuth();
  const router = useRouter();
  const navigate = useNavigate();
  const search = Route.useSearch();
  const handleSignIn = async (loginType: LoginType) => {
    await auth.login(loginType, search.deviceCode);
    await router.invalidate();
    await navigate({ to: search.redirect || fallback });
  };
  const isLocal = process.env.NODE_ENV === "development";
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
            <>
              <GithubButton
                onClick={() => handleSignIn(LoginType.GIT_HUB_O_AUTH)}
              >
                Sign in with GitHub
              </GithubButton>
              <GoogleButton
                variant='outline'
                onClick={() => handleSignIn(LoginType.GOOGLE_O_AUTH)}
              >
                Sign in with Google
              </GoogleButton>
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
};
