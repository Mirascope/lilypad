import {
  ChevronDown,
  ScrollText,
  Table,
  // Parentheses,
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
  SidebarMenuSub,
} from "@/components/ui/sidebar";
import {
  Collapsible,
  CollapsibleTrigger,
  CollapsibleContent,
} from "@/components/ui/collapsible";
import { Link, useNavigate } from "@tanstack/react-router";
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
        <SidebarMenuButton className={depth > 0 ? "ml-4" : ""}>
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
  const { user } = useAuth();
  const navigate = useNavigate();
  const auth = useAuth();
  const { data: projects } = useSuspenseQuery(projectsQueryOptions());
  const organizationMutation = useUpdateActiveOrganizationMutation();
  const projectList: Item[] = projects.map((project) => ({
    title: project.name,
    url: `/projects/${project.uuid}/functions`,
    children: [
      {
        title: "Generations",
        url: `/projects/${project.uuid}/generations`,
        icon: Table,
      },
      // {
      //   title: "New Function",
      //   url: `/projects/${project.uuid}/functions`,
      //   icon: Parentheses,
      // },
    ],
  }));
  const items: Item[] = [
    {
      title: "Projects",
      url: "/projects",
      icon: ScrollText,
      children: projectList,
    },
  ];
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
