import { useAuth } from "@/auth";
import { CreateOrganizationDialog } from "@/components/OrganizationDialog";
import { AppHeader } from "@/components/sidebar/AppHeader";
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from "@/components/ui/collapsible";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Separator } from "@/components/ui/separator";
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
import { fetchAnnotationsByProjectUuid } from "@/ee/utils/annotations";
import { Route as ProjectRoute } from "@/routes/_auth/projects/$projectUuid.index";
import { ProjectPublic } from "@/types/types";
import { fetchLatestVersionUniqueFunctionNames, functionKeys } from "@/utils/functions";
import { projectsQueryOptions } from "@/utils/projects";
import { fetchSpans } from "@/utils/spans";
import { useUpdateActiveOrganizationMutation } from "@/utils/users";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams, useRouter } from "@tanstack/react-router";
import {
  Blocks,
  ChevronDown,
  ChevronsUpDown,
  Logs,
  NotebookPen,
  Plus,
  ScrollText,
  Settings,
  SquareFunction,
  User2,
} from "lucide-react";
import { useEffect, useState } from "react";
import { toast } from "sonner";
interface Item {
  title: string;
  url: string;
  icon?: React.ElementType;
  children?: Item[];
  onHover?: () => void;
}
const RecursiveMenuContent = ({
  item,
  depth = 0,
  onHover,
}: {
  item: Item;
  depth?: number;
  onHover?: () => void;
}) => {
  const hasChildren = item.children && item.children.length > 0;
  if (!hasChildren) {
    return (
      <SidebarMenuItem onMouseEnter={() => onHover?.()} onFocus={() => onHover?.()}>
        <SidebarMenuButton className={`m-0 px-4 ${depth > 0 ? "ml-6" : ""}`} asChild size="lg">
          <Link
            to={item.url}
            className="[&.active]:text-accent-foreground [&.active]:bg-accent flex w-full items-center gap-2 [&.active]:font-extrabold"
          >
            {item.icon && <item.icon className="h-4 w-4" />}
            <span>{item.title}</span>
          </Link>
        </SidebarMenuButton>
      </SidebarMenuItem>
    );
  }
  return (
    <Collapsible defaultOpen className={`group/collapsible-${depth.toString()}`}>
      <SidebarMenuItem>
        <CollapsibleTrigger asChild>
          <SidebarMenuButton className={depth > 0 ? "ml-4" : ""}>
            {item.icon && <item.icon className="h-4 w-4" />}
            <span>{item.title}</span>
            <ChevronDown
              className={`ml-auto transition-transform group-data-[state=open]/collapsible-${depth.toString()}:rotate-180`}
            />
          </SidebarMenuButton>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <SidebarMenuSub className="nested-menu">
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
  const { activeProject, setProject, user } = useAuth();
  const navigate = useNavigate();
  const [createOrganizationOpen, setCreateOrganizationOpen] = useState<boolean>(false);
  const params = useParams({ strict: false });
  const auth = useAuth();
  const queryClient = useQueryClient();
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
          title: "Traces",
          url: `/projects/${activeProject.uuid}/traces`,
          icon: Logs,
          onHover: () => {
            queryClient
              .prefetchQuery({
                queryKey: ["projects", activeProject.uuid, "traces"],
                queryFn: () => fetchSpans(activeProject.uuid),
              })
              .catch(() => toast.error("Failed to prefetch traces"));
          },
        },
        {
          title: "Functions",
          url: `/projects/${activeProject.uuid}/functions`,
          icon: SquareFunction,
          onHover: () => {
            queryClient
              .prefetchQuery({
                queryKey: ["projects", activeProject.uuid, ...functionKeys.list("unique")],
                queryFn: () => fetchLatestVersionUniqueFunctionNames(activeProject.uuid),
              })
              .catch(() => toast.error("Failed to prefetch functions"));
          },
        },
        {
          title: "Annotations",
          url: `/projects/${activeProject.uuid}/annotations`,
          icon: NotebookPen,
          onHover: () => {
            queryClient
              .prefetchQuery({
                queryKey: ["projects", activeProject.uuid, "annotations"],
                queryFn: () => fetchAnnotationsByProjectUuid(activeProject.uuid),
              })
              .catch(() => toast.error("Failed to prefetch annotations"));
          },
        },
        {
          title: "Playground",
          url: `/projects/${activeProject.uuid}/playground`,
          icon: Blocks,
        },
      ]
    : [];
  const handleOrganizationSwitch = async (organizationUuid: string) => {
    if (user?.active_organization_uuid == organizationUuid) return;
    router
      .invalidate()
      .catch(() => toast.error("Failed to invalidate."))
      .finally(() => {
        navigate({
          to: "/projects",
          replace: true,
        }).catch(() => toast.error("Failed to navigate"));
      });
    setProject(null);
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
    const projectPathMatch = /\/projects\/[^/]+(?:\/([^/]+))?/.exec(currentPath);
    if (projectPathMatch) {
      const currentSection = projectPathMatch[1] || "";
      const newPath = currentSection
        ? `/projects/${project.uuid}/${currentSection}`
        : `/projects/${project.uuid}`;

      navigate({ to: newPath, replace: true }).catch(() => toast.error("Failed to navigate"));
    } else {
      navigate({ to: currentPath, replace: true }).catch(() => toast.error("Failed to navigate"));
    }
  };
  const renderProjectSelector = () => {
    return (
      <SidebarMenu>
        <SidebarGroup className="flex gap-1">
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  size="lg"
                  tooltip="Projects" // Add tooltip for collapsed state
                >
                  <ScrollText />
                  <span>{activeProject ? activeProject.name : "Select Project"}</span>
                  <ChevronDown className="ml-auto" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
                align="start"
                side="right"
                sideOffset={4}
              >
                {projects.map((project) => (
                  <DropdownMenuItem key={project.uuid} onClick={() => handleProjectChange(project)}>
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
                  onHover={item.onHover}
                />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarMenu>
    );
  };
  const renderOrganizationsDropdownItems = () => {
    return (
      <>
        {user?.user_organizations?.map((user_organization) => (
          <DropdownMenuCheckboxItem
            key={user_organization.uuid}
            onClick={() => handleOrganizationSwitch(user_organization.organization.uuid)}
            checked={user_organization.organization.uuid === user.active_organization_uuid}
          >
            {user_organization.organization.name}
          </DropdownMenuCheckboxItem>
        ))}
      </>
    );
  };
  return (
    <>
      <Sidebar collapsible="icon" className="lilypad-sidebar default:font-fun">
        <SidebarHeader>
          <AppHeader activeProject={activeProject} to={ProjectRoute.fullPath} />
        </SidebarHeader>
        <SidebarContent>{renderProjectSelector()}</SidebarContent>
        <Separator className="mt-2" />
        <SidebarFooter>
          <SidebarMenu>
            <SidebarMenuItem>
              <SidebarMenuButton asChild size="lg">
                <Link
                  to={"/settings/$"}
                  params={{ _splat: "overview" }}
                  className="[&.active]:text-accent-foreground [&.active]:bg-accent flex w-full items-center gap-2 [&.active]:font-extrabold"
                >
                  <Settings className="h-4 w-4" />
                  <span>{"Settings"}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
            <SidebarMenuItem>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <SidebarMenuButton size="lg">
                    <User2 /> {user?.first_name}
                    <ChevronsUpDown className="ml-auto" />
                  </SidebarMenuButton>
                </DropdownMenuTrigger>
                <DropdownMenuContent
                  className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
                  align="start"
                  side="right"
                  sideOffset={4}
                >
                  {renderOrganizationsDropdownItems()}
                  <DropdownMenuItem
                    onSelect={() => {
                      setCreateOrganizationOpen(true);
                    }}
                    className="flex gap-2"
                  >
                    <Plus className="h-4 w-4" />
                    Create Organization
                  </DropdownMenuItem>
                  <DropdownMenuItem onClick={handleLogout}>Logout</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </SidebarMenuItem>
          </SidebarMenu>
        </SidebarFooter>
        <SidebarRail />
      </Sidebar>
      <CreateOrganizationDialog
        key="create-organization"
        open={createOrganizationOpen}
        setOpen={setCreateOrganizationOpen}
      />
    </>
  );
};

export default AppSidebar;
