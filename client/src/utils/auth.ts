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
  try {
    const response = await fetch(
      "https://mirascope.com/static/content-meta/policy/index.json"
    );

    if (!response.ok) {
      throw new Error(`Failed to fetch policy data: ${response.status}`);
    }

    const policyData = await response.json();

    // Find the privacy policy and terms of service entries
    const privacyPolicy = policyData.find(
      (policy: any) => policy.slug === "privacy"
    );
    const termsOfService = policyData.find(
      (policy: any) => policy.slug === "service"
    );

    if (!privacyPolicy || !termsOfService) {
      throw new Error("Could not find required policy information");
    }

    return {
      privacyVersion: privacyPolicy.lastUpdated,
      termsVersion: termsOfService.lastUpdated,
    };
  } catch (error) {
    console.error("Error fetching versions:", error);
    throw error;
  }
};
