import { useAuth } from "@/auth";
import { useToast } from "@/hooks/use-toast";
import { UserConsentUpdate } from "@/types/types";
import { callbackCodeQueryOptions } from "@/utils/auth";
import {
  useCreateUserConsentMutation,
  useUpdateUserConsentMutation,
} from "@/utils/user_consents";
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
  const { toast } = useToast();
  const { code, state } = Route.useSearch();
  let stateJson: State = {};

  if (state) {
    try {
      stateJson = JSON.parse(atob(state));
    } catch (e) {
      console.error("Failed to parse state:", e);
    }
  }
  const activeProvider = stateJson.provider ?? "github";
  // TODO: make these dynamic
  const termsVersion = "2025-04-04";
  const privacyVersion = "2025-04-04";

  const { data: session } = useSuspenseQuery(
    callbackCodeQueryOptions(activeProvider, privacyVersion, termsVersion, code)
  );
  const createUserConsent = useCreateUserConsentMutation();
  const updateUserConsent = useUpdateUserConsentMutation();
  useEffect(() => {
    if (session) {
      auth.setSession(session);
    }
  }, [session]);

  useEffect(() => {
    if (auth.user) {
      if (!auth.user.user_consents) {
        if (!createUserConsent.isPending) {
          createUserConsent.mutate({
            privacy_policy_version: privacyVersion,
            tos_version: termsVersion,
          });
        }
      } else {
        const updates: UserConsentUpdate = {};
        if (auth.user.user_consents.privacy_policy_version !== privacyVersion) {
          updates.privacy_policy_version = privacyVersion;
        }
        if (auth.user.user_consents.tos_version !== termsVersion) {
          updates.tos_version = termsVersion;
        }
        if (Object.keys(updates).length > 0) {
          updateUserConsent.mutate({
            userConsentUuid: auth.user.user_consents.uuid,
            userConsentUpdate: updates,
          });
        }
      }
      navigate({
        to: stateJson?.redirect ?? "/projects",
        from: "/",
      }).catch(() => {
        toast({
          title: "Error",
          description: "Failed to navigate after login.",
          variant: "destructive",
        });
      });
    }
  }, [stateJson.redirect, auth.user]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <h2 className="text-xl">Processing login...</h2>
        <p className="text-gray-500 mt-2">
          Authenticating with {activeProvider}...
        </p>
      </div>
    </div>
  );
};
