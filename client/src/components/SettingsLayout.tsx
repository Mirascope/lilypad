import { LucideIcon, SettingsIcon } from "lucide-react";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
export const SettingsLayout = ({
  children,
  icon: Icon = SettingsIcon,
  title,
}: {
  children: React.ReactNode;
  icon?: LucideIcon;
  title?: string;
}) => {
  return (
    <div className='min-h-screen bg-gray-50 p-8'>
      <div className='max-w-4xl mx-auto'>
        <Card>
          <CardHeader className='flex flex-row justify-center items-center gap-2'>
            <Icon className='w-8 h-8 text-gray-700' />
            <h2 className='text-2xl font-semibold'>{title}</h2>
          </CardHeader>
          <CardContent className='p-6'>{children}</CardContent>
        </Card>
      </div>
    </div>
  );
};
