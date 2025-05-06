import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { JSX, useState } from "react";

export interface Tab {
  label: string;
  value: string;
  component?: JSX.Element | null;
  isDisabled?: boolean;
}

export const TabGroup = ({
  tabs,
  className,
  handleTabChange,
}: {
  tabs: Tab[];
  handleTabChange?: (tab: string) => void;
  className?: string;
}) => {
  const [tab, setTab] = useState<string>(tabs[0].value);
  const onTabChange = (value: string) => {
    setTab(value);
    handleTabChange?.(value);
  };
  return (
    <div
      className={cn(
        "bg-primary/20 border-primary/20 rounded-md border-1 px-2 py-2 shadow-md h-full flex flex-col",
        className
      )}
    >
      <Tabs
        value={tab}
        onValueChange={onTabChange}
        className="w-full flex flex-col h-full"
      >
        <div className="flex flex-col gap-1 h-full">
          <div className="shrink-0 flex px-1">
            <TabsList className="h-auto gap-x-2 bg-transparent p-0 font-roboto">
              {tabs.map((tab) => (
                <TabsTrigger
                  key={tab.value}
                  value={tab.value}
                  disabled={tab.isDisabled}
                >
                  {tab.label}
                </TabsTrigger>
              ))}
            </TabsList>
          </div>

          <div className="grow overflow-hidden bg-white rounded-md border-1">
            {tabs.map((tab) => (
              <TabsContent
                key={tab.value}
                value={tab.value}
                className="h-full overflow-auto m-0 p-0"
              >
                {tab.component}
              </TabsContent>
            ))}
          </div>
        </div>
      </Tabs>
    </div>
  );
};
