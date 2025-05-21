import { LilypadLogo } from "@/components/lilypad-logo";
import { Badge } from "@/components/ui/badge";
import { SidebarMenu, SidebarMenuButton, SidebarMenuItem } from "@/components/ui/sidebar";
import { Typography } from "@/components/ui/typography";
import { ProjectPublic } from "@/types/types";
import { useNavigate } from "@tanstack/react-router";
import { toast } from "sonner";

interface AppHeaderProps {
  to: string;
  activeProject?: ProjectPublic | null;
}
export const AppHeader = ({ to, activeProject }: AppHeaderProps) => {
  const navigate = useNavigate();
  const handleProjectClick = () => {
    if (activeProject) {
      navigate({
        to,
        params: {
          projectUuid: activeProject.uuid,
        },
      }).catch(() => toast.error("Failed to navigate"));
    } else {
      navigate({
        to: "/",
      }).catch(() => toast.error("Failed to navigate"));
    }
  };
  return (
    <SidebarMenu>
      <SidebarMenuItem>
        <SidebarMenuButton
          size="logo"
          className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
          onClick={handleProjectClick}
        >
          <div className="text-sidebar-primary-foreground flex aspect-square items-center justify-center rounded-lg">
            <LilypadLogo size={34} />
          </div>
          <Typography variant="h4" className="flex flex-1 items-center gap-2">
            <span className="text-primary fun truncate">Lilypad</span>
            <Badge className="text-primary bg-yellow-400 hover:bg-yellow-500">Beta</Badge>
          </Typography>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  );
};
