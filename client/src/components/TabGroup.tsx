import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
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
        "bg-card rounded-md border-1 pt-2 shadow-md h-full flex flex-col",
        className
      )}
    >
      <Tabs
        value={tab}
        onValueChange={onTabChange}
        className="w-full flex flex-col h-full"
      >
        <div className="flex flex-col gap-1 h-full">
          <ScrollArea>
            <div className="w-full relative h-10 px-2">
              <TabsList className="h-10 flex absolute gap-x-2 bg-transparent p-0 font-handwriting">
                {tabs
                  .filter((tab) => tab.component)
                  .map((tab) => (
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
            <ScrollBar orientation="horizontal" />
          </ScrollArea>

          <div className="grow overflow-hidden bg-white border-t-1">
            {tabs.map((tab) => (
              <TabsContent
                key={tab.value}
                value={tab.value}
                className="w-fullh-full overflow-auto m-0 p-0"
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
