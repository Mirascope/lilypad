import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Typography } from "@/components/ui/typography";
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
    <div className="bg-gray-50 p-8">
      <div className="max-w-4xl mx-auto">
        <Card>
          <CardHeader className="flex flex-row justify-center items-center gap-2">
            <Icon className="w-8 h-8 text-gray-700" />
            {typeof title === "string" ? (
              <Typography variant="h3">{title}</Typography>
            ) : (
              title
            )}
          </CardHeader>
          <CardContent className="p-6">{children}</CardContent>
        </Card>
      </div>
    </div>
  );
};
