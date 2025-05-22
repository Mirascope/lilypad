import { LilypadLogo } from "@/components/lilypad-logo";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarRail,
} from "@/components/ui/sidebar";
import { Skeleton } from "@/components/ui/skeleton";

const SidebarSkeleton = () => {
  return (
    <Sidebar collapsible="icon" className="lilypad-sidebar">
      <SidebarHeader>
        <SidebarHeader>
          <SidebarMenuButton>
            <LilypadLogo /> Lilypad
          </SidebarMenuButton>
        </SidebarHeader>
      </SidebarHeader>

      <SidebarContent>
        <SidebarMenu>
          <SidebarGroup>
            <SidebarMenuItem>
              <div className="flex items-center gap-2 px-3 py-2">
                <Skeleton className="h-4 w-4" />
                <Skeleton className="h-4 w-32" />
                <Skeleton className="ml-auto h-4 w-4" />{" "}
              </div>
            </SidebarMenuItem>

            <SidebarGroupContent>
              <SidebarMenu>
                {["Home", "Functions", "Prompts"].map((_, index) => (
                  <SidebarMenuItem key={index}>
                    <div className="flex items-center gap-2 px-3 py-2">
                      <Skeleton className="h-4 w-4" />
                      <Skeleton className="h-4 w-24" />
                    </div>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        </SidebarMenu>
      </SidebarContent>

      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <div className="flex items-center gap-2 px-3 py-2">
              <Skeleton className="h-4 w-4" />
              <Skeleton className="h-4 w-16" />
            </div>
          </SidebarMenuItem>

          <SidebarMenuItem>
            <div className="flex items-center gap-2 px-3 py-2">
              <Skeleton className="h-4 w-4" />
              <Skeleton className="h-4 w-20" />
              <Skeleton className="ml-auto h-4 w-4" />
            </div>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>

      <SidebarRail />
    </Sidebar>
  );
};

export default SidebarSkeleton;
