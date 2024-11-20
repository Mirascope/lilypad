import {
  redirect,
  createFileRoute,
  useRouter,
  useNavigate,
} from "@tanstack/react-router";

import { useAuth } from "@/auth";
import { Button } from "@/components/ui/button";
import { LoginType } from "@/types/types";

const fallback = "/projects" as const;
export const Route = createFileRoute("/auth/login")({
  validateSearch: (search) => {
    return { redirect: (search.redirect as string) || undefined };
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
    await auth.login(loginType);
    await router.invalidate();
    await navigate({ to: search.redirect || fallback });
  };

  return (
    <div>
      <Button onClick={() => handleSignIn(LoginType.GIT_HUB_O_AUTH)}>
        GitHub
      </Button>
      <Button onClick={() => handleSignIn(LoginType.GOOGLE_O_AUTH)}>
        Google
      </Button>
    </div>
  );
};
