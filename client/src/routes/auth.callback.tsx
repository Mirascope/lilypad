import { useAuth } from "@/auth";
import { callbackCodeQueryOptions } from "@/utils/auth";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";

type SearchParam = {
  code: string;
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
    return { code };
  },
  component: () => <CallbackPage />,
});

const CallbackPage = () => {
  const auth = useAuth();
  const navigate = useNavigate();
  const { code } = Route.useSearch();
  const { data: session } = useSuspenseQuery(callbackCodeQueryOptions(code));
  useEffect(() => {
    auth.setSession(session);
  }, [session]);

  useEffect(() => {
    if (auth.user) navigate({ to: "/projects" });
  }, [auth.user]);

  return (
    <div className='min-h-screen flex items-center justify-center'>
      <div className='text-center'>
        <h2 className='text-xl'>Processing login...</h2>
      </div>
    </div>
  );
};
