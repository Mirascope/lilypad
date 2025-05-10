import { ScrollArea, ScrollBar } from "@/components/ui/scroll-area";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { Outlet } from "@tanstack/react-router";
import { JSX, ReactNode, useEffect, useState } from "react";

export interface Tab {
  label: string | ReactNode;
  value: string;
  component?: JSX.Element | null;
  isDisabled?: boolean;
}

export const TabGroup = ({
  tabs,
  tab: initialTab,
  className,
  handleTabChange,
}: {
  tabs: Tab[];
  handleTabChange?: (tab: string) => void;
  className?: string;
  tab?: string;
}) => {
  // Find the first tab that has a component and is not disabled
  const findFirstEligibleTab = () => {
    return tabs.find((tab) => tab.component && !tab.isDisabled)?.value ?? "";
  };
  const [tab, setTab] = useState<string>(initialTab ?? findFirstEligibleTab());

  // Set the initial tab when the component mounts or when tabs change
  useEffect(() => {
    if (initialTab) return;
    const firstEligibleTabValue = findFirstEligibleTab();
    setTab(firstEligibleTabValue);
    // Optionally notify parent about the initial tab selection
    if (firstEligibleTabValue && handleTabChange) {
      handleTabChange(firstEligibleTabValue);
    }
  }, [tabs]); // Re-run when tabs array changes

  const onTabChange = (value: string) => {
    setTab(value);
    handleTabChange?.(value);
  };

  if (tabs.length === 0) return null;

  return (
    <div
      className={cn(
        "bg-card rounded-md border-1 p-2 shadow-md h-full flex flex-col",
        className
      )}
    >
      <Tabs
        value={tab}
        onValueChange={onTabChange}
        className="w-full flex flex-col h-full"
      >
        <div className="flex flex-col h-full">
          <ScrollArea className="mb-1">
            <div className="w-full relative h-10 px-2">
              <TabsList className="h-10 flex absolute gap-x-2 bg-transparent p-0 font-handwriting">
                {tabs
                  .filter((tab) => tab.component)
                  .map((tab) => (
                    <TabsTrigger
                      className="relative"
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

          <div className="flex-1 min-h-0 bg-white border-t-1 rounded-md">
            {tabs.map((tab) => (
              <TabsContent
                key={tab.value}
                value={tab.value}
                className="w-full h-full data-[state=active]:flex data-[state=active]:flex-col m-0 p-0"
              >
                {tab.component ?? <Outlet />}
              </TabsContent>
            ))}
          </div>
        </div>
      </Tabs>
    </div>
  );
};
