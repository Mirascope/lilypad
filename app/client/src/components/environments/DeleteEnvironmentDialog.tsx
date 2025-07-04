import { useAuth } from "@/src/auth";
import { Button } from "@/src/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/src/components/ui/dialog";
import { cn } from "@/src/lib/utils";
import { EnvironmentPublic } from "@/src/types/types";
import { useDeleteEnvironmentMutation } from "@/src/utils/environments";
import { Trash } from "lucide-react";
import { toast } from "sonner";
export const DeleteEnvironmentDialog = ({ environment }: { environment: EnvironmentPublic }) => {
  const deleteEnvironment = useDeleteEnvironmentMutation();
  const { setEnvironment } = useAuth();

  const handleEnvironmentDelete = async (environmentUuid: string) => {
    await deleteEnvironment
      .mutateAsync(environmentUuid)
      .catch(() => toast.error("Failed to delete environment"));

    setEnvironment(null);
    toast.success("Successfully deleted environment");
  };

  return (
    <Dialog>
      <DialogTrigger asChild onClick={(e) => e.stopPropagation()}>
        <Button variant="outlineDestructive" size="icon" className="h-8 w-8">
          <Trash />
        </Button>
      </DialogTrigger>
      <DialogContent className={cn("max-w-[425px] overflow-x-auto")}>
        <DialogHeader className="shrink-0">
          <DialogTitle>{`Delete ${environment.name}`}</DialogTitle>
          <DialogDescription>This action is final and cannot be undone.</DialogDescription>
          <p>
            {"Are you sure you want to delete "}
            <b>{environment.name}</b>?
          </p>
        </DialogHeader>

        <DialogFooter>
          <Button variant="destructive" onClick={() => handleEnvironmentDelete(environment.uuid)}>
            Delete
          </Button>
          <DialogClose asChild>
            <Button type="button" variant="secondary">
              Cancel
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
