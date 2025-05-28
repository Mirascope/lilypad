import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { APIKeyPublic } from "@/types/types";
import { useDeleteApiKeyMutation } from "@/utils/api-keys";
import { Trash } from "lucide-react";
import { toast } from "sonner";
export const DeleteAPIKeyDialog = ({ apiKey }: { apiKey: APIKeyPublic }) => {
  const deleteApiKey = useDeleteApiKeyMutation();
  const handleApiKeyDelete = async (apiKeyUuid: string) => {
    await deleteApiKey.mutateAsync(apiKeyUuid).catch(() => toast.error("Failed to delete API Key"));
    toast.success("Successfully deleted API Key");
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
          <DialogTitle>{`Delete ${apiKey.name}`}</DialogTitle>
          <DialogDescription>This action is final and cannot be undone.</DialogDescription>
          <p>
            {"Are you sure you want to delete "}
            <b>{apiKey.name}</b>?
          </p>
        </DialogHeader>

        <DialogFooter>
          <Button variant="destructive" onClick={() => handleApiKeyDelete(apiKey.uuid)}>
            Delete
          </Button>
          <DialogClose asChild>
            <Button type="button" variant="secondary">
              Close
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
