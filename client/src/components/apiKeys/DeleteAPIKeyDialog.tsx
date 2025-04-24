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
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";
import { APIKeyPublic } from "@/types/types";
import { useDeleteApiKeyMutation } from "@/utils/api-keys";
import { Trash } from "lucide-react";
export const DeleteAPIKeyDialog = ({ apiKey }: { apiKey: APIKeyPublic }) => {
  const { toast } = useToast();
  const deleteApiKey = useDeleteApiKeyMutation();
  const handleApiKeyDelete = async (apiKeyUuid: string) => {
    const res = await deleteApiKey.mutateAsync(apiKeyUuid);
    if (res) {
      toast({
        title: "Successfully deleted API Key",
      });
    } else {
      toast({
        title: "Failed to delete API Key",
        variant: "destructive",
      });
    }
  };
  return (
    <Dialog>
      <DialogTrigger asChild onClick={(e) => e.stopPropagation()}>
        <Button variant='outlineDestructive' size='icon' className='h-8 w-8'>
          <Trash />
        </Button>
      </DialogTrigger>
      <DialogContent className={cn("max-w-[425px] overflow-x-auto")}>
        <DialogHeader className='flex-shrink-0'>
          <DialogTitle>{`Delete ${apiKey.name}`}</DialogTitle>
          <DialogDescription>
            This action is final and cannot be undone.
          </DialogDescription>
          <p>
            {"Are you sure you want to delete "}
            <b>{apiKey.name}</b>?
          </p>
        </DialogHeader>

        <DialogFooter>
          <Button
            variant='destructive'
            onClick={() => handleApiKeyDelete(apiKey.uuid)}
          >
            Delete
          </Button>
          <DialogClose asChild>
            <Button type='button' variant='secondary'>
              Close
            </Button>
          </DialogClose>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
