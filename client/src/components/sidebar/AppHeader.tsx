import { LilypadIcon } from "@/components/LilypadIcon";
import { Badge } from "@/components/ui/badge";
import {
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
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
        {/* <SidebarMenuButton
          size="logo"
          className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
        >
          <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
            <GalleryVerticalEnd className="size-4" />
          </div>
          <div className="grid flex-1 text-left text-sm leading-tight">
            <span className="truncate font-semibold">Acme Inc</span>
            <span className="truncate text-xs">Enterprise</span>
          </div>
        </SidebarMenuButton> */}
        <SidebarMenuButton
          size="logo"
          className="data-[state=open]:bg-sidebar-accent data-[state=open]:text-sidebar-accent-foreground"
          onClick={handleProjectClick}
        >
          <div className="flex aspect-square size-8 items-center justify-center rounded-lg text-sidebar-primary-foreground">
            <LilypadIcon className="size-10" />
          </div>
          <Typography variant="h4" className="flex items-center gap-2 flex-1">
            <span className="truncate">Lilypad</span>
            <Badge className="bg-yellow-400 text-primary hover:bg-yellow-500">
              Beta
            </Badge>
          </Typography>
        </SidebarMenuButton>
      </SidebarMenuItem>
    </SidebarMenu>
  );
};
