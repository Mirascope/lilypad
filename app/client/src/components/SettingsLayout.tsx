import { Card, CardContent, CardHeader } from "@/src/components/ui/card";
import { Typography } from "@/src/components/ui/typography";
import { LucideIcon, SettingsIcon } from "lucide-react";
import { ReactNode } from "react";
export const SettingsLayout = ({
  children,
  icon: Icon = SettingsIcon,
  title,
}: {
  children: ReactNode;
  icon?: LucideIcon;
  title?: string | ReactNode;
}) => {
  return (
    <div className="bg-muted p-8">
      <div className="mx-auto max-w-4xl">
        <Card>
          <CardHeader className="flex flex-row items-center justify-center gap-2">
            <Icon className="h-8 w-8 text-gray-700" />
            {typeof title === "string" ? <Typography variant="h3">{title}</Typography> : title}
          </CardHeader>
          <CardContent className="p-6">{children}</CardContent>
        </Card>
      </div>
    </div>
  );
};
