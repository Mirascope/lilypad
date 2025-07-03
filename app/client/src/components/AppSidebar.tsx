import { useAuth } from "@/src/auth";
import { CreateOrganizationDialog } from "@/src/components/OrganizationDialog";
import { AppHeader } from "@/src/components/sidebar/AppHeader";
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from "@/src/components/ui/collapsible";
import {
  DropdownMenu,
  DropdownMenuCheckboxItem,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/src/components/ui/dropdown-menu";
import { Separator } from "@/src/components/ui/separator";
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
} from "@/src/components/ui/sidebar";
import { useEnvironmentQueries } from "@/src/hooks/use-environment-queries";
import { Route as ProjectRoute } from "@/src/routes/_auth/projects/$projectUuid.index";
import { EnvironmentPublic, ProjectPublic } from "@/src/types/types";
import { environmentsQueryOptions } from "@/src/utils/environments";
import { projectsQueryOptions } from "@/src/utils/projects";
import { useUpdateActiveOrganizationMutation } from "@/src/utils/users";
import { useQueryClient, useSuspenseQuery } from "@tanstack/react-query";
import { Link, useNavigate, useParams, useRouter } from "@tanstack/react-router";
import {
  Blocks,
  ChevronDown,
  ChevronsUpDown,
  Globe,
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
            className="flex w-full items-center gap-2 [&.active]:bg-accent [&.active]:font-extrabold [&.active]:text-accent-foreground"
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
  const { activeProject, setProject, activeEnvironment, setEnvironment, user } = useAuth();
  const navigate = useNavigate();
  const [createOrganizationOpen, setCreateOrganizationOpen] = useState<boolean>(false);
  const params = useParams({ strict: false });
  const auth = useAuth();
  const queryClient = useQueryClient();
  const { data: projects } = useSuspenseQuery(projectsQueryOptions());
  const { data: environments } = useSuspenseQuery(environmentsQueryOptions());
  const environmentQueries = useEnvironmentQueries();
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
            const queryOptions = environmentQueries.spansQueryOptions(activeProject.uuid);
            queryClient
              .prefetchQuery({
                queryKey: queryOptions.queryKey,
                queryFn: queryOptions.queryFn,
              })
              .catch(() => toast.error("Failed to prefetch traces"));
          },
        },
        {
          title: "Functions",
          url: `/projects/${activeProject.uuid}/functions`,
          icon: SquareFunction,
          onHover: () => {
            const queryOptions = environmentQueries.uniqueLatestVersionFunctionNamesQueryOptions(
              activeProject.uuid
            );
            queryClient
              .prefetchQuery({
                queryKey: queryOptions.queryKey,
                queryFn: queryOptions.queryFn,
              })
              .catch(() => toast.error("Failed to prefetch functions"));
          },
        },
        {
          title: "Annotations",
          url: `/projects/${activeProject.uuid}/annotations`,
          icon: NotebookPen,
          onHover: () => {
            const queryOptions = environmentQueries.annotationsByProjectQueryOptions(
              activeProject.uuid
            );
            queryClient
              .prefetchQuery({
                queryKey: queryOptions.queryKey,
                queryFn: queryOptions.queryFn,
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

  const handleEnvironmentChange = (environment: EnvironmentPublic) => {
    setEnvironment(environment);
    queryClient.invalidateQueries({
      predicate: (query) => query.queryKey.some(key => 
        typeof key === 'string' && key.toLowerCase().includes('project')
      )
    });
  };

  const renderProjectSelector = () => {
    return (
      <SidebarMenu>
        <SidebarGroup className="flex gap-1">
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  size="sm"
                  className={`border border-dashed ${
                    activeEnvironment?.is_development
                      ? "border-amber-400 bg-amber-50 text-amber-900 hover:bg-amber-100 dark:border-amber-600 dark:bg-amber-950 dark:text-amber-100 dark:hover:bg-amber-900"
                      : "border-blue-400 bg-blue-50 text-blue-900 hover:bg-blue-100 dark:border-blue-600 dark:bg-blue-950 dark:text-blue-100 dark:hover:bg-blue-900"
                  }`}
                  tooltip="Environment"
                >
                  <Globe className="h-4 w-4" />
                  <span className="truncate">
                    {activeEnvironment ? activeEnvironment.name : "Select Environment"}
                  </span>
                  <ChevronDown className="ml-auto h-3 w-3" />
                </SidebarMenuButton>
              </DropdownMenuTrigger>
              <DropdownMenuContent
                className="w-[--radix-dropdown-menu-trigger-width] min-w-56 rounded-lg"
                align="start"
                side="right"
                sideOffset={4}
              >
                {environments?.map((environment) => (
                  <DropdownMenuItem
                    key={environment.uuid}
                    onClick={() => handleEnvironmentChange(environment)}
                    className={
                      environment.is_development
                        ? "text-amber-700 dark:text-amber-300"
                        : "text-blue-700 dark:text-blue-300"
                    }
                  >
                    <div className="flex items-center gap-2">
                      <div
                        className={`h-2 w-2 rounded-full ${
                          environment.is_development ? "bg-amber-500" : "bg-blue-500"
                        }`}
                      />
                      <span>{environment.name}</span>
                      {environment.is_development && (
                        <span className="ml-auto text-xs text-muted-foreground">DEV</span>
                      )}
                    </div>
                  </DropdownMenuItem>
                ))}
              </DropdownMenuContent>
            </DropdownMenu>
          </SidebarMenuItem>
          <SidebarMenuItem>
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <SidebarMenuButton
                  size="lg"
                  tooltip="Projects"
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
          {activeProject && (
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
          )}
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
                  className="flex w-full items-center gap-2 [&.active]:bg-accent [&.active]:font-extrabold [&.active]:text-accent-foreground"
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
