import { Compass, GlobeLock, ScrollText } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/router";

interface DocsMenuItemProps {
  title: string;
  path: string;
  Icon: React.ElementType;
  isActive: boolean;
}

const DocsMenuItem = ({ title, path, Icon, isActive }: DocsMenuItemProps) => {
  return (
    <Link
      href={path}
      className={`group mb-3 flex flex-row items-center gap-3 ${isActive ? "_text-primary-800 dark:_text-primary-600" : "text-gray-500 dark:_bg-primary-400/10"} hover:text-primary/100 text-md`}
    >
      <Icon className={`w-8 h-8 p-1 border rounded ${isActive ? "_bg-primary-100 dark:_bg-primary-400/10" : ""} group-hover:bg-border/30`} />
      {title}
    </Link>
  );
};

export const DocsMenuSeparator = () => {
  const { asPath } = useRouter();
  
  const menuItems = [
    { title: "Docs", path: "/docs", Icon: ScrollText },
    { title: "Guides", path: "/guides", Icon: Compass },
    { title: "Self Hosting", path: "/self-hosting", Icon: GlobeLock },
  ];

  return (
    <div className="-mx-2 hidden md:block">
      {menuItems.map((item) => (
        <DocsMenuItem
          key={item.path}
          title={item.title}
          path={item.path}
          Icon={item.Icon}
          isActive={asPath.startsWith(item.path)}
        />
      ))}
    </div>
  );
};
