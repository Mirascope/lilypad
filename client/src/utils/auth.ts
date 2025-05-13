import api from "@/api";
import { UserPublic } from "@/types/types";
import { queryOptions } from "@tanstack/react-query";
export const fetchGitHubCallbackCode = async (code: string) => {
  const params = new URLSearchParams({ code });
  return (
    await api.get<UserPublic>(`/auth/github/callback?${params.toString()}`)
  ).data;
};

export const fetchGoogleCallbackCode = async (code: string) => {
  const params = new URLSearchParams({ code });
  return (
    await api.get<UserPublic>(`/auth/google/callback?${params.toString()}`)
  ).data;
};

export const callbackCodeQueryOptions = (provider: string, code?: string) =>
  queryOptions({
    queryKey: ["user"],
    queryFn: async () => {
      if (!code) {
        return null;
      }
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

export const fetchVersions = async () => {
  const privacyResponse = await fetch("https://mirascope.com/privacy");
  const termsResponse = await fetch("https://mirascope.com/terms/service");

  const privacyHtml = await privacyResponse.text();
  const termsHtml = await termsResponse.text();

  const privacyParser = new DOMParser();
  const termsParser = new DOMParser();

  const privacyDoc = privacyParser.parseFromString(privacyHtml, "text/html");
  const termsDoc = termsParser.parseFromString(termsHtml, "text/html");

  const privacyVersion = privacyDoc.querySelector(".last-updated-time");
  const termsVersion = termsDoc.querySelector(".last-updated-time");

  if (
    !privacyVersion ||
    !termsVersion ||
    !privacyVersion.textContent ||
    !termsVersion.textContent
  ) {
    throw new Error("Could not find version information");
  }
  return {
    privacyVersion: privacyVersion.textContent,
    termsVersion: termsVersion.textContent,
  };
};
