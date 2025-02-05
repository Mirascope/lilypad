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
          deviceCode: search.deviceCode as string,
        },
      });
    }
    return { code, state: search.state as string };
  },
  component: () => <CallbackPage />,
});

type State = {
  deviceCode?: string;
  redirect?: string;
};
const CallbackPage = () => {
  const auth = useAuth();
  const navigate = useNavigate();
  const { code, state } = Route.useSearch();
  let stateJson: State = {};
  if (state) {
    stateJson = JSON.parse(atob(state));
  }
  const { data: session } = useSuspenseQuery(
    callbackCodeQueryOptions(code, stateJson?.deviceCode)
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
      </div>
    </div>
  );
};
