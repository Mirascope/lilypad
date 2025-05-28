import { Button, ButtonProps } from "@/components/ui/button";
import { UserConsentDialog } from "@/components/UserConsentDialog";
import { settingsQueryOptions } from "@/utils/settings";
import { useSuspenseQuery } from "@tanstack/react-query";
import { ReactNode, useState } from "react";
interface GithubButtonProps extends ButtonProps {
  iconSize?: number;
  iconColor?: string;
  children?: ReactNode;
}

const GithubButton = ({
  iconSize = 24,
  iconColor = "currentColor",
  children,
  ...buttonProps
}: GithubButtonProps) => {
  return (
    <Button {...buttonProps} className="cursor-pointer bg-[#333333] hover:bg-[#555555]">
      <svg
        fill={iconColor}
        role="img"
        viewBox="0 0 24 24"
        width={iconSize}
        height={iconSize}
        xmlns="http://www.w3.org/2000/svg"
        className="mr-2"
      >
        <path d="M12 .297c-6.63 0-12 5.373-12 12 0 5.303 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61C4.422 18.07 3.633 17.7 3.633 17.7c-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.092 24 17.592 24 12.297c0-6.627-5.373-12-12-12" />
      </svg>
      {children}
    </Button>
  );
};

export const GithubLogin = ({ redirect, showModal }: { redirect?: string; showModal: boolean }) => {
  const { data: settings } = useSuspenseQuery(settingsQueryOptions());
  const [open, setOpen] = useState<boolean>(false);

  const getAuthUrl = () => {
    const githubAuthUrl = "https://github.com/login/oauth/authorize";
    const params = new URLSearchParams({
      client_id: settings.github_client_id,
      redirect_uri: `${settings.remote_client_url}/auth/callback`,
      scope: "read:user user:email",
      response_type: "code",
    });
    const stateObject = {
      provider: "github",
      ...(redirect && { redirect }),
    };

    const state = btoa(JSON.stringify(stateObject));
    params.append("state", state);
    return `${githubAuthUrl}?${params.toString()}`;
  };

  const handleGithubLogin = () => {
    window.location.href = getAuthUrl();
  };

  return (
    <>
      <GithubButton
        onClick={() => {
          if (showModal) {
            setOpen(true);
          } else {
            handleGithubLogin();
          }
        }}
      >
        Login with GitHub
      </GithubButton>
      <UserConsentDialog open={open} setOpen={setOpen} onClick={handleGithubLogin} />
    </>
  );
};
