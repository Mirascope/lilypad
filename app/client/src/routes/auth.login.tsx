import { createFileRoute, redirect } from "@tanstack/react-router";

import { useAuth } from "@/src/auth";
import { GithubLogin } from "@/src/components/GithubLogin";
import { GoogleLogin } from "@/src/components/GoogleLogin";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/src/components/ui/card";
import { fetchVersions } from "@/src/utils/auth";
import { useEffect, useState } from "react";

interface LoginSearchParam {
  redirect?: string;
}

const fallback = "/projects";
export const Route = createFileRoute("/auth/login")({
  validateSearch: (search): LoginSearchParam => {
    return {
      redirect: (search.redirect as string) || undefined,
    };
  },
  beforeLoad: ({ context, search }) => {
    if (context.auth.isAuthenticated) {
      throw redirect({
        to: search.redirect ?? fallback,
      });
    }
  },
  component: () => <LoginComponent />,
});

export const LoginComponent = () => {
  const { redirect } = Route.useSearch();
  const [showModal, setShowModal] = useState<boolean>(false);
  const { loadPrivacyPolicyVersion, loadTermsVersion } = useAuth();
  useEffect(() => {
    const checkVersions = async () => {
      try {
        const { privacyVersion, termsVersion } = await fetchVersions();
        const storedPrivacyVersion = loadPrivacyPolicyVersion();
        const storedTermsVersion = loadTermsVersion();

        const versionsChanged =
          storedPrivacyVersion !== privacyVersion || storedTermsVersion !== termsVersion;

        setShowModal(!!versionsChanged);
      } catch (error) {
        console.error("Error checking versions:", error);
        setShowModal(false);
      }
    };

    checkVersions();
  }, []);
  return (
    <div className="flex h-screen items-center justify-center">
      <Card className="m-0 w-[600px]">
        <CardHeader>
          <CardTitle>Welcome to Lilypad</CardTitle>
          <CardDescription>Sign in to continue</CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col gap-2">
          <GithubLogin redirect={redirect} showModal={showModal} />
          <GoogleLogin redirect={redirect} showModal={showModal} />
        </CardContent>
      </Card>
    </div>
  );
};
