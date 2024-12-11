import { useAuth } from "@/auth";
import { useToast } from "@/hooks/use-toast";
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
};
const CallbackPage = () => {
  const auth = useAuth();
  const navigate = useNavigate();
  const { code, state } = Route.useSearch();
  const { toast } = useToast();
  let stateJson: State = {};
  if (state) {
    stateJson = JSON.parse(atob(state));
  }
  const { data: session } = useSuspenseQuery(
    callbackCodeQueryOptions(code, stateJson?.deviceCode)
  );

  useEffect(() => {
    auth.setSession(session);
    if (session)
      toast({
        title: "Successfully authenticated",
        description: "You may now close this window and proceed in the CLI.",
      });
  }, [session]);

  useEffect(() => {
    if (auth.user)
      navigate({
        to: "/projects",
        search: { redirect: undefined, deviceCode: undefined },
      });
  }, [auth.user]);

  return (
    <div className='min-h-screen flex items-center justify-center'>
      <div className='text-center'>
        <h2 className='text-xl'>Processing login...</h2>
      </div>
    </div>
  );
};
