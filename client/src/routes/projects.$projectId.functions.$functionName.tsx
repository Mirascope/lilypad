import { createFileRoute, Outlet } from "@tanstack/react-router";
import { SelectVersionForm } from "@/components/SelectVerisonForm";

export const Route = createFileRoute(
  "/projects/$projectId/functions/$functionName"
)({
  component: () => {
    return (
      <div className='w-full'>
        <SelectVersionForm />
        <Outlet />
      </div>
    );
  },
});
