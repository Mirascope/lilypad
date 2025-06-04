import { useAuth } from "@/src/auth";
import { UserConsentUpdate } from "@/src/types/types";
import { callbackCodeQueryOptions, fetchVersions } from "@/src/utils/auth";
import {
  useCreateUserConsentMutation,
  useUpdateUserConsentMutation,
} from "@/src/utils/user_consents";
import { useSuspenseQuery } from "@tanstack/react-query";
import { createFileRoute, redirect, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { toast } from "sonner";

interface SearchParam {
  code: string;
  state?: string;
}
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

interface State {
  redirect?: string;
  provider?: string;
}

const CallbackPage = () => {
  const auth = useAuth();
  const navigate = useNavigate();
  const { code, state } = Route.useSearch();
  const { setPrivacyPolicyVersion, setTermsVersion } = useAuth();
  let stateJson: State = {};

  if (state) {
    try {
      stateJson = JSON.parse(atob(state));
    } catch (e) {
      console.error("Failed to parse state:", e);
    }
  }
  const activeProvider = stateJson.provider ?? "github";

  const { data: session } = useSuspenseQuery(callbackCodeQueryOptions(activeProvider, code));
  const createUserConsent = useCreateUserConsentMutation();
  const updateUserConsent = useUpdateUserConsentMutation();
  useEffect(() => {
    if (session) {
      auth.setSession(session);
    }
  }, [session]);

  useEffect(() => {
    if (!auth.user) return;
    const run = async () => {
      const { privacyVersion, termsVersion } = await fetchVersions();
      setPrivacyPolicyVersion(privacyVersion);
      setTermsVersion(termsVersion);

      if (auth.user) {
        if (!auth.user.user_consents) {
          if (!createUserConsent.isPending) {
            createUserConsent
              .mutateAsync({
                privacy_policy_version: privacyVersion,
                tos_version: termsVersion,
              })
              .catch(() => toast.error("Failed to save privacy and terms"));
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
            updateUserConsent
              .mutateAsync({
                userConsentUuid: auth.user.user_consents.uuid,
                userConsentUpdate: updates,
              })
              .catch(() => toast.error("Failed to update privacy and terms"));
          }
        }
        navigate({
          to: stateJson?.redirect ?? "/projects",
          from: "/",
        }).catch(() => {
          toast.error("Failed to navigate after login.");
        });
      }
    };
    run();
  }, [stateJson?.redirect, auth.user]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="text-center">
        <h2 className="text-xl">Processing login...</h2>
        <p className="mt-2 text-gray-500">Authenticating with {activeProvider}...</p>
      </div>
    </div>
  );
};
