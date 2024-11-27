import {
  ChevronDown,
  ChevronRight,
  ScrollText,
  Table,
  Parentheses,
  User2,
  ChevronUp,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useRouter } from "@tanstack/react-router";
import { projectsQueryOptions } from "@/utils/projects";
import { useAuth } from "@/auth";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuCheckboxItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useUpdateActiveOrganizationMutation } from "@/utils/auth";

const RecursiveMenuContent = ({ item, depth = 0 }) => {
  const [isExpanded, setIsExpanded] = useState(false);
  const hasChildren = item.children && item.children.length > 0;

  const handleClick = (e) => {
    if (hasChildren) {
      e.preventDefault();
      setIsExpanded(!isExpanded);
    }
  };

  return (
    <>
      <SidebarMenuButton
        asChild={!hasChildren}
        className={`w-full ${depth > 0 ? "ml-4" : ""}`}
        onClick={hasChildren ? handleClick : undefined}
      >
        {hasChildren ? (
          <div className='flex items-center w-full gap-2'>
            {item.icon && <item.icon className='w-4 h-4' />}
            <span>{item.title}</span>
            {isExpanded ? (
              <ChevronDown className='w-4 h-4 ml-auto' />
            ) : (
              <ChevronRight className='w-4 h-4 ml-auto' />
            )}
          </div>
        ) : (
          <Link
            to={item.url}
            className='flex items-center w-full gap-2 [&.active]:font-bold'
          >
            {item.icon && <item.icon className='w-4 h-4' />}
            <span>{item.title}</span>
          </Link>
        )}
      </SidebarMenuButton>

      {hasChildren && isExpanded && (
        <SidebarMenu className='ml-4 relative before:absolute before:left-2 before:top-0 before:h-full before:w-px before:bg-gray-200'>
          {item.children.map((child, index) => (
            <SidebarMenuItem key={`${child.title}-${index}`}>
              <RecursiveMenuContent item={child} depth={depth + 1} />
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
      )}
    </>
  );
};

export const AppSidebar = () => {
  const router = useRouter();
  const { user } = useAuth();
  const navigate = useNavigate();
  const auth = useAuth();
  const { data: projects } = useSuspenseQuery(projectsQueryOptions());
  const organizationMutation = useUpdateActiveOrganizationMutation();
  const projectList = projects.map((project) => ({
    title: project.name,
    url: `/projects/${project.id}/functions`,
    children: [
      {
        title: "Traces",
        url: `/projects/${project.id}/traces`,
        icon: Table,
      },
      {
        title: "New Function",
        url: `/projects/${project.id}/functions`,
        icon: Parentheses,
      },
    ],
  }));
  const items = [
    {
      title: "Projects",
      url: "/projects",
      icon: ScrollText,
      children: projectList,
    },
  ];
  const handleOrganizationSwitch = async (organizationId: string) => {
    if (user?.organization_id == organizationId) return;
    const newSession = await organizationMutation.mutateAsync({
      organizationId,
    });
    auth.setSession(newSession);
  };
  const handleLogout = () => {
    auth.logout().then(() => {
      router.invalidate().finally(() => {
        navigate({ to: "/auth/login", search: { redirect: undefined } });
      });
    });
  };
  const renderOrganizationsDropdownItems = () => {
    return user?.user_organizations.map((user_organization) => (
      <DropdownMenuCheckboxItem
        key={user_organization.id}
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
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Lilypad</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {items.map((item, index) => (
                <RecursiveMenuContent
                  key={`${item.title}-${index}`}
                  item={item}
                />
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarFooter>
        <SidebarMenu>
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
    </Sidebar>
  );
};

export default AppSidebar;
