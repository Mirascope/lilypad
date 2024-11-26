import { Button } from "@/components/ui/button";
import { SlackLogo } from "@/components/SlackLogo";

export const CommunityButton = () => {
  return (
    <a
      href="https://join.slack.com/t/mirascope-community/shared_invite/zt-2ilqhvmki-FB6LWluInUCkkjYD3oSjNA"
      className="no-underline"
    >
      <Button variant="secondary" size="lg" className="sm:w-fit w-full border">
        <SlackLogo width="18" height="18" />
        Community
      </Button>
    </a>
  );
};
