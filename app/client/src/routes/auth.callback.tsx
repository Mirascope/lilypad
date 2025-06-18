import { useAuth } from "@/src/auth";
import { callbackCodeQueryOptions } from "@/src/utils/auth";
import { settingsQueryOptions } from "@/src/utils/settings";
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
  const { data: settings } = useSuspenseQuery(settingsQueryOptions());
  const createUserConsent = useCreateUserConsentMutation();
  const updateUserConsent = useUpdateUserConsentMutation();
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

  useEffect(() => {
    if (session) {
      auth.setSession(session);
    }
  }, [session]);

  useEffect(() => {
    if (!auth.user) return;

    const { privacy_version, terms_version } = settings;
    const { user_consents } = auth.user;

    if (privacy_version && terms_version) {
      if (!user_consents && !createUserConsent.isPending) {
        createUserConsent
          .mutateAsync({ privacy_policy_version: privacy_version, tos_version: terms_version })
          .catch(() => toast.error("Failed to save privacy and terms"));
      } else if (user_consents) {
        const updates = {
          ...(user_consents.privacy_policy_version !== privacy_version && {
            privacy_policy_version: privacy_version,
          }),
          ...(user_consents.tos_version !== terms_version && { tos_version: terms_version }),
        };

        if (Object.keys(updates).length > 0) {
          updateUserConsent
            .mutateAsync({
              userConsentUuid: user_consents.uuid,
              userConsentUpdate: updates,
            })
            .catch(() => toast.error("Failed to update privacy and terms"));
        }
      }

      setPrivacyPolicyVersion(privacy_version);
      setTermsVersion(terms_version);
    }

    navigate({
      to: stateJson?.redirect ?? "/projects",
      from: "/",
    }).catch(() => toast.error("Failed to navigate after login."));
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
