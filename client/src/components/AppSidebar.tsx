import { useAuth } from "@/auth";
import { LilypadIcon } from "@/components/LilypadIcon";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/components/ui/collapsible";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
  SidebarMenuSub,
  SidebarRail,
} from "@/components/ui/sidebar";
import { Route as ProjectRoute } from "@/routes/_auth/projects/$projectUuid.index";
import { ProjectPublic } from "@/types/types";
import { projectsQueryOptions } from "@/utils/projects";
import {
  userQueryOptions,
  useUpdateActiveOrganizationMutation,
} from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import {
  Link,
  useNavigate,
  useParams,
  useRouter,
} from "@tanstack/react-router";
import {
  ChevronDown,
  ChevronUp,
  Home,
  NotebookPen,
  ScrollText,
  Settings,
  SquareTerminal,
  User2,
  Wrench,
} from "lucide-react";
import { useEffect } from "react";
import { toast } from "sonner";
interface Item {
  title: string;
  url: string;
  icon?: React.ElementType;
  children?: Item[];
}
const RecursiveMenuContent = ({
  item,
  depth = 0,
}: {
  item: Item;
  depth?: number;
}) => {
  const hasChildren = item.children && item.children.length > 0;
  if (!hasChildren) {
    return (
      <SidebarMenuItem>
        <SidebarMenuButton className={depth > 0 ? "ml-4" : ""} asChild>
          <Link
            to={item.url}
            className='flex items-center w-full gap-2 [&.active]:font-bold'
          >
            {item.icon && <item.icon className='w-4 h-4' />}
            <span>{item.title}</span>
          </Link>
        </SidebarMenuButton>
      </SidebarMenuItem>
    );
  }
  return (
    <Collapsible
      defaultOpen
      className={`group/collapsible-${depth.toString()}`}
    >
      <SidebarMenuItem>
        <CollapsibleTrigger asChild>
          <SidebarMenuButton className={depth > 0 ? "ml-4" : ""}>
            {item.icon && <item.icon className='w-4 h-4' />}
            <span>{item.title}</span>
            <ChevronDown
              className={`ml-auto transition-transform group-data-[state=open]/collapsible-${depth.toString()}:rotate-180`}
            />
          </SidebarMenuButton>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <SidebarMenuSub className='nested-menu'>
            {item.children?.map((child, index) => (
              <RecursiveMenuContent
                key={`${child.title}-${index}`}
                item={child}
                depth={depth + 1}
              />
            ))}
          </SidebarMenuSub>
        </CollapsibleContent>
      </SidebarMenuItem>
    </Collapsible>
  );
};
export const AppSidebar = () => {
  const router = useRouter();
  const { activeProject, setProject } = useAuth();
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const navigate = useNavigate();
  const params = useParams({ strict: false });
  const auth = useAuth();
  const { data: projects } = useSuspenseQuery(projectsQueryOptions());
  useEffect(() => {
    if (!params?.projectUuid) return;
    const project = projects?.find((p) => p.uuid === params?.projectUuid);
    setProject(project);
  }, [projects, params, setProject]);

  const organizationMutation = useUpdateActiveOrganizationMutation();
  const projectItems: Item[] = activeProject
    ? [
        {
          title: "Home",
          url: `/projects/${activeProject.uuid}/traces`,
          icon: Home,
        },
        {
          title: "Functions",
          url: `/projects/${activeProject.uuid}/functions`,
          icon: Wrench,
        },
        {
          title: "Annotations",
          url: `/projects/${activeProject.uuid}/annotations`,
          icon: NotebookPen,
        },
        {
          title: "Playground",
          url: `/projects/${activeProject.uuid}/playground`,
          icon: SquareTerminal,
        },
      ]
    : [];
  const handleOrganizationSwitch = async (organizationUuid: string) => {
    if (user?.active_organization_uuid == organizationUuid) return;
    const newSession = await organizationMutation.mutateAsync({
      organizationUuid,
    });
    auth.setSession(newSession);
  };
  const handleLogout = () => {
    auth.logout();
    router
      .invalidate()
      .catch(() => toast.error("Failed to invalidate."))
      .finally(() => {
        navigate({
          to: "/auth/login",
        }).catch(() => toast.error("Failed to navigate"));
      });
  };
  const handleProjectChange = (project: ProjectPublic) => {
    setProject(project);
    const currentPath = window.location.pathname;

    const projectPathMatch = /\/projects\/[^/]+(?:\/([^/]+))?/.exec(
      currentPath
    );
    if (projectPathMatch) {
      const currentSection = projectPathMatch[1] || "";
      const newPath = currentSection
        ? `/projects/${project.uuid}/${currentSection}`
        : `/projects/${project.uuid}`;

      navigate({ to: newPath, replace: true }).catch(() =>
        toast.error("Failed to navigate")
      );
    } else {
      navigate({ to: currentPath, replace: true }).catch(() =>
        toast.error("Failed to navigate")
      );
    }
  };
  const renderProjectSelector = () => {
    return (
      <SidebarMenu>
        <SidebarGroup>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton>
                  <ScrollText />
                  {activeProject ? activeProject.name : "Select Project"}
                  <ChevronDown className='ml-auto' />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent className='w-[--radix-popper-anchor-width]'>
                {projects.map((project) => (
                  <DropdownMenuItem
                    key={project.uuid}
                    onClick={() => handleProjectChange(project)}
                  >
                    {project.name}
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
          <SidebarGroupContent>
            <SidebarMenu>
              {projectItems.map((item, index) => (
                <RecursiveMenuContent
                  key={`${item.title}-${index}`}
                  item={item}
                />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarMenu>
    );
  };
  const renderOrganizationsDropdownItems = () => {
    return user?.user_organizations?.map((user_organization) => (
      <DropdownMenuCheckboxItem
        key={user_organization.uuid}
        onClick={() =>
          void handleOrganizationSwitch(user_organization.organization.uuid)
        }
        checked={
          user_organization.organization.uuid === user.active_organization_uuid
        }
      >
        {user_organization.organization.name}
      </DropdownMenuCheckboxItem>
    ));
  };
  return (
    <Sidebar collapsible='icon' className='lilypad-sidebar'>
      <SidebarHeader>
        <SidebarMenuButton asChild>
          <Link
            {...(activeProject
              ? {
                  to: ProjectRoute.fullPath,
                  params: { projectUuid: activeProject.uuid },
                }
              : { to: "/" })}
          >
            <LilypadIcon /> Lilypad
          </Link>
        </SidebarMenuButton>
      </SidebarHeader>
      <SidebarContent>{renderProjectSelector()}</SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild>
              <Link
                to={"/settings/$"}
                className='flex items-center w-full gap-2 [&.active]:font-bold'
              >
                <Settings />
                Settings
              </Link>
            </SidebarMenuButton>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton>
                  <User2 /> {user?.first_name}
                  <ChevronUp className='ml-auto' />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                side='top'
                className='w-[--radix-popper-anchor-width]'
              >
                {renderOrganizationsDropdownItems()}
                <DropdownMenuItem onClick={handleLogout}>
                  Logout
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarFooter>
      <SidebarRail />
    </Sidebar>
  );
};

export default AppSidebar;
