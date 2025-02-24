import { useAuth } from "@/auth";
import { callbackCodeQueryOptions } from "@/utils/auth";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";

type SearchParam = {
  code: string;
  state?: string;
};
export const Route = createFileRoute("/auth/callback")({
  validateSearch: (search): SearchParam => {
    const code = search.code;
    if (typeof code !== "string" || !code) {
      throw redirect({
        to: "/auth/login",
        search: {
          redirect: location.href,
        },
      });
    }
    return { code, state: search.state as string };
  },
  component: () => <CallbackPage />,
});

type State = {
  redirect?: string;
  provider?: string;
};

const CallbackPage = () => {
  const auth = useAuth();
  const navigate = useNavigate();
  const { code, state } = Route.useSearch();
  let stateJson: State = {};

  if (state) {
    try {
      stateJson = JSON.parse(atob(state));
    } catch (e) {
      console.error("Failed to parse state:", e);
    }
  }
  const activeProvider = stateJson.provider || "github";

  const { data: session } = useSuspenseQuery(
    callbackCodeQueryOptions(activeProvider, code)
  );

  useEffect(() => {
    auth.setSession(session);
  }, [session]);

  useEffect(() => {
    if (auth.user) {
      navigate({
        to: stateJson?.redirect || "/projects",
        from: "/",
      });
    }
  }, [stateJson.redirect, auth.user]);

  return (
    <div className='min-h-screen flex items-center justify-center'>
      <div className='text-center'>
        <h2 className='text-xl'>Processing login...</h2>
        <p className='text-gray-500 mt-2'>
          Authenticating with {activeProvider}...
        </p>
      </div>
    </div>
  );
};
