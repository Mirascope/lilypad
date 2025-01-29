import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  useCreateUserOrganizationMutation,
  userQueryOptions,
} from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  createFileRoute,
  useNavigate,
  useParams,
} from "@tanstack/react-router";
import { useEffect, useState } from "react";

export const Route = createFileRoute("/join/$token")({
  component: () => <JoinPage />,
});

const JoinPage = () => {
  const { token } = useParams({ from: Route.id });
  const createUserOrganization = useCreateUserOrganizationMutation();
  const navigate = useNavigate();
  const [isProcessing, setIsProcessing] = useState(true);
  const [error, setError] = useState("");

  const { data: user } = useSuspenseQuery(userQueryOptions());

  useEffect(() => {
    const processInvite = async () => {
      try {
        if (!token) {
          setError("Invalid invite link");
          return;
        }

        if (user) {
          await createUserOrganization.mutateAsync();
          navigate({
            to: "/projects",
            search: { joined: true },
          });
        } else {
          navigate({
            to: "/auth/login",
            search: { redirect: Route.fullPath },
          });
        }
      } catch (err: unknown) {
        if (err instanceof Error) {
          setError(err.message);
        } else if (typeof err === "string") {
          setError(err);
        } else {
          setError("Failed to process invite");
        }
      } finally {
        setIsProcessing(false);
      }
    };

    processInvite();
  }, [token, user, navigate]);

  if (isProcessing) {
    return (
      <div className='flex items-center justify-center min-h-screen'>
        <div className='text-center'>
          <div className='animate-spin rounded-full h-12 w-12 border-b-2 border-gray-900 mx-auto mb-4' />
          <p className='text-gray-600'>Processing your invite...</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className='p-4'>
        <Alert variant='destructive'>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      </div>
    );
  }

  return null;
};

export default JoinPage;
