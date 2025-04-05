import api from "@/api";
import { UserPublic } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";
export const fetchGitHubCallbackCode = async (
  privacyVersion: string,
  termsVersion: string,
  code: string
) => {
  const params = new URLSearchParams({ privacyVersion, termsVersion, code });
  return (
    await api.get<UserPublic>(`/auth/github/callback?${params.toString()}`)
  ).data;
};

export const fetchGoogleCallbackCode = async (
  privacyVersion: string,
  termsVersion: string,
  code: string
) => {
  const params = new URLSearchParams({ privacyVersion, termsVersion, code });
  return (
    await api.get<UserPublic>(`/auth/google/callback?${params.toString()}`)
  ).data;
};

export const callbackCodeQueryOptions = (
  provider: string,
  privacyVersion: string,
  termsVersion: string,
  code?: string
) =>
  queryOptions({
    queryKey: ["user"],
    queryFn: async () => {
      if (!code) {
        return null;
      }
      if (provider === "github") {
        return await fetchGitHubCallbackCode(
          privacyVersion,
          termsVersion,
          code
        );
      } else if (provider === "google") {
        return await fetchGoogleCallbackCode(
          privacyVersion,
          termsVersion,
          code
        );
      } else {
        return null;
      }
    },
    enabled: Boolean(code),
  });
