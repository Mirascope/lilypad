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

  // Create DOM parsers to extract the information
  const privacyParser = new DOMParser();
  const termsParser = new DOMParser();

  const privacyDoc = privacyParser.parseFromString(privacyHtml, "text/html");
  const termsDoc = termsParser.parseFromString(termsHtml, "text/html");

  // Find all divs with h1 and p that match the structure
  const privacyDivs = privacyDoc.querySelectorAll("div");
  const termsDivs = termsDoc.querySelectorAll("div");

  let privacyVersion: string | undefined = undefined;
  let termsVersion: string | undefined = undefined;
  // Search through privacy divs to find the matching structure
  for (const div of privacyDivs) {
    const h1 = div.querySelector("h1.text-3xl.font-bold.uppercase");
    const p = div.querySelector("p.text-muted-foreground");

    if (h1 && p && h1.textContent?.includes("Privacy Policy")) {
      privacyVersion = p.textContent?.replace("Last Updated:", "").trim();
      break;
    }
  }

  // Search through terms divs to find the matching structure
  for (const div of termsDivs) {
    const h1 = div.querySelector("h1.text-3xl.font-bold.uppercase");
    const p = div.querySelector("p.text-muted-foreground");

    if (h1 && p && h1.textContent?.includes("Terms of Service")) {
      termsVersion = p.textContent?.replace("Last Updated:", "").trim();
      break;
    }
  }

  if (!privacyVersion || !termsVersion) {
    throw new Error("Could not find version information");
  }
  return { privacyVersion, termsVersion };
};
