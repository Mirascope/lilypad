import SidebarSkeleton from "@/src/components/SidebarSkeleton";
import { SidebarProvider } from "@/src/components/ui/sidebar";
import { Skeleton } from "@/src/components/ui/skeleton";

const MainContent = () => (
  <div className="grid h-full w-full grid-cols-1 gap-4 p-4 md:grid-cols-2 lg:grid-cols-3">
    {[...Array(6)].map((_, i) => (
      <div key={i} className="min-h-32 rounded-lg bg-background p-4 shadow">
        <Skeleton className="mb-4 h-4 w-3/4" />
        <Skeleton className="h-4 w-full" />
      </div>
    ))}
  </div>
);

export const LayoutSkeleton = () => {
  return (
    <div className="flex h-screen border-collapse overflow-hidden">
      <SidebarProvider>
        <SidebarSkeleton />
        <main className="flex-1 overflow-x-hidden overflow-y-auto bg-muted pt-4 pb-1">
          <MainContent />
        </main>
      </SidebarProvider>
    </div>
  );
};
