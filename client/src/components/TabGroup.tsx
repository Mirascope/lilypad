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

  // Initialize state with initialTab or first eligible tab
  const [tab, setTab] = useState<string>(initialTab ?? findFirstEligibleTab());

  // Update internal state when initialTab prop changes
  useEffect(() => {
    if (initialTab !== undefined) {
      setTab(initialTab);
    } else if (!tab) {
      // If no tab is selected yet and no initialTab provided, set to first eligible
      const firstEligibleTabValue = findFirstEligibleTab();
      setTab(firstEligibleTabValue);
      // Notify parent about the initial tab selection
      if (firstEligibleTabValue && handleTabChange) {
        handleTabChange(firstEligibleTabValue);
      }
    }
  }, [initialTab, tabs]);

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
          <ScrollArea className="mb-2">
            <div className="w-full relative h-8">
              <TabsList className="h-8 flex absolute gap-x-2 bg-transparent p-0 ">
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
