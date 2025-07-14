import { useAuth } from "@/src/auth";
import { Alert, AlertDescription } from "@/src/components/ui/alert";
import { organizationInviteQueryOptions } from "@/src/utils/organizations";
import { useCreateUserOrganizationMutation } from "@/src/utils/users";
import { useQuery } from "@tanstack/react-query";
import { createFileRoute, redirect, useNavigate, useParams } from "@tanstack/react-router";
import { useEffect } from "react";

export const Route = createFileRoute("/join/$token")({
  beforeLoad: ({ params, context }) => {
    const { token } = params;
    if (!context.auth.isAuthenticated) {
      throw redirect({
        to: "/auth/login",
        search: {
          redirect: `join/${token}`,
        },
      });
    }
  },
  component: () => <JoinPage />,
});

export const JoinPage = () => {
  const { token } = useParams({ from: Route.id });
  const {
    data: organizationInvite,
    isLoading,
    isError,
  } = useQuery(organizationInviteQueryOptions(token));
  const createUserOrganization = useCreateUserOrganizationMutation();
  const navigate = useNavigate();
  const { user, setSession } = useAuth();

  useEffect(() => {
    const processInvite = async () => {
      if (user && organizationInvite) {
        const newSession = await createUserOrganization.mutateAsync(token);
        setSession(newSession);
        navigate({
          to: "/projects",
          search: { joined: true },
        });
      }
    };
    if (isLoading) return;
    processInvite();
  }, [organizationInvite, user, isLoading]);

  if (isLoading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <div className="text-center">
          <div className="mx-auto mb-4 h-12 w-12 animate-spin rounded-full border-b-2 border-gray-900" />
          <p className="text-gray-600">Processing your invite...</p>
        </div>
      </div>
    );
  }

  if (isError) {
    return (
      <div className="p-4">
        <Alert variant="destructive">
          <AlertDescription>Invalid invite link</AlertDescription>
        </Alert>
      </div>
    );
  }

  return null;
};
