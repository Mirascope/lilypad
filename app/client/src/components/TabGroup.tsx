import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/src/components/ui/tabs";
import { cn } from "@/src/lib/utils";
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
    }
  }, [initialTab]);

  useEffect(() => {
    // If no tab is selected yet and no initialTab provided, set to first eligible
    const findTab = tabs.find((tab) => tab.value === initialTab);
    if (!findTab) {
      const firstEligibleTabValue = findFirstEligibleTab();
      setTab(firstEligibleTabValue);
      if (firstEligibleTabValue && handleTabChange) {
        handleTabChange(firstEligibleTabValue);
      }
    }
  }, [tabs]);
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
    <div className={cn("flex h-full flex-col rounded-md border bg-card p-2 shadow-md", className)}>
      <Tabs value={tab} onValueChange={onTabChange} className="flex h-full w-full flex-col">
        <div className="flex h-full flex-col">
          <div className="relative mb-2">
            {/* Left Arrow Button */}
            <button
              onClick={scrollLeft}
              className={`absolute top-1/2 left-0 z-10 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full bg-background/60 shadow-md backdrop-blur-sm transition-opacity duration-200 ${showLeftArrow ? "pointer-events-auto opacity-100" : "pointer-events-none opacity-0"}`}
              aria-label="Scroll tabs left"
              aria-hidden={!showLeftArrow}
            >
              <ChevronLeft className="h-3 w-3" />
            </button>

            {/* Scrollable Tabs Container */}
            <div
              ref={tabsListRef}
              className="relative no-scrollbar h-8 overflow-x-auto overflow-y-hidden"
              onScroll={handleScroll}
            >
              <TabsList className="flex h-8 gap-x-2 bg-transparent p-0 default:font-fun">
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
                `absolute top-1/2 right-0 z-10 flex h-6 w-6 -translate-y-1/2 items-center justify-center rounded-full bg-background/60 shadow-md backdrop-blur-sm transition-opacity duration-200`,
                showRightArrow ? "opacity-100" : "pointer-events-none opacity-0"
              )}
              aria-label="Scroll tabs right"
              tabIndex={showRightArrow ? 0 : -1}
            >
              <ChevronRight className="h-3 w-3" />
            </button>
          </div>

          <div className="min-h-0 flex-1 rounded-md border-t bg-background">
            {tabs.map((tab) => (
              <TabsContent
                key={tab.value}
                value={tab.value}
                className="m-0 h-full w-full p-0 data-[state=active]:flex data-[state=active]:flex-col"
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
