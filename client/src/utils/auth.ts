import api from "@/api";
import { UserPublic } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";
export const fetchGitHubCallbackCode = async (code?: string) => {
  if (!code) {
    return null;
  }
  const params = new URLSearchParams({ code });
  return (
    await api.get<UserPublic>(`/auth/github/callback?${params.toString()}`)
  ).data;
};

export const fetchGoogleCallbackCode = async (code?: string) => {
  if (!code) {
    return null;
  }
  const params = new URLSearchParams({ code });
  return (
    await api.get<UserPublic>(`/auth/google/callback?${params.toString()}`)
  ).data;
};

export const callbackCodeQueryOptions = (provider: string, code?: string) =>
  queryOptions({
    queryKey: ["user"],
    queryFn: async () => {
      if (provider === "github") {
        return await fetchGitHubCallbackCode(code);
      } else if (provider === "google") {
        return await fetchGoogleCallbackCode(code);
      } else {
        return null;
      }
    },
    enabled: Boolean(code),
  });
