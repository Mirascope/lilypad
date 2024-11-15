import {
  ChevronDown,
  ChevronRight,
  ScrollText,
  Table,
  Parentheses,
} from "lucide-react";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from "@/components/ui/sidebar";
import { Link } from "@tanstack/react-router";
import { useState } from "react";
import { useSuspenseQuery } from "@tanstack/react-query";
import { projectsQueryOptions } from "@/utils/projects";

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
  const { data: projects } = useSuspenseQuery(projectsQueryOptions());
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
    </Sidebar>
  );
};

export default AppSidebar;
