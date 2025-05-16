import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { cn } from "@/lib/utils";
import { Outlet } from "@tanstack/react-router";
import { ChevronLeft, ChevronRight } from "lucide-react";
import { JSX, ReactNode, useEffect, useRef, useState } from "react";

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
  const tabsListRef = useRef<HTMLDivElement>(null);
  const [showLeftArrow, setShowLeftArrow] = useState(false);
  const [showRightArrow, setShowRightArrow] = useState(false);

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

  // Check if scrolling is needed and update arrow visibility
  useEffect(() => {
    const checkScroll = () => {
      if (tabsListRef.current) {
        const { scrollLeft, scrollWidth, clientWidth } = tabsListRef.current;
        setShowLeftArrow(scrollLeft > 0);
        setShowRightArrow(scrollLeft < scrollWidth - clientWidth);
      }
    };

    checkScroll();
    window.addEventListener("resize", checkScroll);

    // Setup a mutation observer to detect when tabs change
    const observer = new MutationObserver(checkScroll);
    if (tabsListRef.current) {
      observer.observe(tabsListRef.current, { childList: true, subtree: true });
    }

    return () => {
      window.removeEventListener("resize", checkScroll);
      observer.disconnect();
    };
  }, [tabs]);

  const onTabChange = (value: string) => {
    setTab(value);
    handleTabChange?.(value);
  };

  const scrollLeft = () => {
    if (tabsListRef.current) {
      tabsListRef.current.scrollBy({ left: -100, behavior: "smooth" });
    }
  };

  const scrollRight = () => {
    if (tabsListRef.current) {
      tabsListRef.current.scrollBy({ left: 100, behavior: "smooth" });
    }
  };

  // Handle scroll events to update arrow visibility
  const handleScroll = () => {
    if (tabsListRef.current) {
      const { scrollLeft, scrollWidth, clientWidth } = tabsListRef.current;
      setShowLeftArrow(scrollLeft > 0);
      setShowRightArrow(scrollLeft < scrollWidth - clientWidth - 1); // -1 for rounding errors
    }
  };

  if (tabs.length === 0) return null;

  return (
    <div
      className={cn(
        "bg-card rounded-md border p-2 shadow-md h-full flex flex-col",
        className
      )}
    >
      <Tabs
        value={tab}
        onValueChange={onTabChange}
        className="w-full flex flex-col h-full"
      >
        <div className="flex flex-col h-full">
          <div className="mb-2 relative">
            {/* Left Arrow Button */}
            <button
              onClick={scrollLeft}
              className={`bg-background/60 absolute top-1/2 left-0 z-10 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full shadow-md backdrop-blur-sm transition-opacity duration-200 ${showLeftArrow ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"}`}
              aria-label="Scroll tabs left"
              aria-hidden={!showLeftArrow}
            >
              <ChevronLeft className="h-3 w-3" />
            </button>

            {/* Scrollable Tabs Container */}
            <div
              ref={tabsListRef}
              className="overflow-x-auto overflow-y-hidden no-scrollbar relative h-8"
              onScroll={handleScroll}
            >
              <TabsList className="h-8 flex gap-x-2 bg-transparent p-0">
                {tabs
                  .filter((tab) => tab.component)
                  .map((tab) => (
                    <TabsTrigger
                      className="relative data-[state=active]:bg-primary dark:data-[state=active]:bg-primary/60"
                      key={tab.value}
                      value={tab.value}
                      disabled={tab.isDisabled}
                    >
                      {tab.label}
                    </TabsTrigger>
                  ))}
              </TabsList>
            </div>

            {/* Right Arrow Button */}
            <button
              onClick={scrollRight}
              className={cn(
                `bg-background/60 absolute top-1/2 right-0 z-10 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full shadow-md backdrop-blur-sm transition-opacity duration-200`,
                showRightArrow ? "opacity-100" : "opacity-0 pointer-events-none"
              )}
              aria-label="Scroll tabs right"
              tabIndex={showRightArrow ? 0 : -1}
            >
              <ChevronRight className="h-3 w-3" />
            </button>
          </div>

          <div className="flex-1 min-h-0 bg-background border-t rounded-md">
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
