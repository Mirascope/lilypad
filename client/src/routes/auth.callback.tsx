import { useAuth } from "@/auth";
import { UserConsentUpdate } from "@/types/types";
import { callbackCodeQueryOptions } from "@/utils/auth";
import { PRIVACY_VERSION, TERMS_VERSION } from "@/utils/constants";
import {
  useCreateUserConsentMutation,
  useUpdateUserConsentMutation,
} from "@/utils/user_consents";
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

  const { data: session } = useSuspenseQuery(
    callbackCodeQueryOptions(
      activeProvider,
      PRIVACY_VERSION,
      TERMS_VERSION,
      code
    )
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
          createUserConsent
            .mutateAsync({
              privacy_policy_version: PRIVACY_VERSION,
              tos_version: TERMS_VERSION,
            })
            .catch(() => toast.error("Failed to save privacy and terms"));
        }
      } else {
        const updates: UserConsentUpdate = {};
        if (
          auth.user.user_consents.privacy_policy_version !== PRIVACY_VERSION
        ) {
          updates.privacy_policy_version = PRIVACY_VERSION;
        }
        if (auth.user.user_consents.tos_version !== TERMS_VERSION) {
          updates.tos_version = TERMS_VERSION;
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
      setPrivacyPolicyVersion(PRIVACY_VERSION);
      setTermsVersion(TERMS_VERSION);
      navigate({
        to: stateJson?.redirect ?? "/projects",
        from: "/",
      }).catch(() => {
        toast.error("Failed to navigate after login.");
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
