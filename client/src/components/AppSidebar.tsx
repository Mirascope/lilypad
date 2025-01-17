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
import { projectsQueryOptions } from "@/utils/projects";
import { useUpdateActiveOrganizationMutation } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Link, useNavigate, useRouter } from "@tanstack/react-router";
import {
  ChevronDown,
  ChevronUp,
  Home,
  PencilLine,
  ScrollText,
  Settings,
  User2,
  Wrench,
} from "lucide-react";
import { useEffect } from "react";

type Item = {
  title: string;
  url: string;
  icon?: React.ElementType;
  children?: Item[];
};
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
  const { user, activeProject, setProject } = useAuth();
  const navigate = useNavigate();
  const auth = useAuth();
  const { data: projects } = useSuspenseQuery(projectsQueryOptions());
  const organizationMutation = useUpdateActiveOrganizationMutation();
  useEffect(() => {
    if (!activeProject && projects.length > 0) {
      setProject(projects[0]);
    }
  }, [activeProject]);
  const projectItems: Item[] = activeProject
    ? [
        {
          title: "Home",
          url: `/projects/${activeProject.uuid}/traces`,
          icon: Home,
        },
        {
          title: "Generations",
          url: `/projects/${activeProject.uuid}/generations`,
          icon: Wrench,
        },
        {
          title: "Prompts",
          url: `/projects/${activeProject.uuid}/prompts`,
          icon: PencilLine,
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
    auth.logout().then(() => {
      router.invalidate().finally(() => {
        navigate({
          to: "/auth/login",
          search: { redirect: undefined },
        });
      });
    });
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
                    onClick={() => setProject(project)}
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
          handleOrganizationSwitch(user_organization.organization.uuid)
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
        <SidebarMenuButton>
          <LilypadIcon /> Lilypad
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
