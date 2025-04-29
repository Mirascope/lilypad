import SidebarSkeleton from "@/components/SidebarSkeleton";
import { SidebarProvider } from "@/components/ui/sidebar";
import { Skeleton } from "@/components/ui/skeleton";

const MainContent = () => (
  <div className="h-full w-full grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 p-4">
    {[...Array(6)].map((_, i) => (
      <div key={i} className="bg-white rounded-lg shadow p-4 min-h-32">
        <Skeleton className="h-4 w-3/4 mb-4" />
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
        <main className="flex-1 overflow-y-auto overflow-x-hidden pt-4 bg-gray-50 pb-1">
          <MainContent />
        </main>
      </SidebarProvider>
    </div>
  );
};
