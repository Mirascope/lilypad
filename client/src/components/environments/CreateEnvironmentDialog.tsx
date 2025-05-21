import { CreateEnvironmentForm } from "@/components/environments/CreateEnvironmentForm";
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
import { PlusCircle } from "lucide-react";

export const CreateEnvironmentDialog = () => {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button
          variant="ghost"
          size="iconSm"
          className="text-primary hover:bg-background hover:text-primary/80"
        >
          <PlusCircle />
        </Button>
      </DialogTrigger>
      <DialogContent className={cn("max-w-[425px] overflow-x-auto")}>
        <DialogHeader className="shrink-0">
          <DialogTitle>Create new Environment</DialogTitle>
        </DialogHeader>
        <DialogDescription>Create an environment for your organization</DialogDescription>
        <CreateEnvironmentForm
          customButtons={
            <DialogFooter>
              <DialogClose asChild>
                <Button type="button" variant="secondary">
                  Cancel
                </Button>
              </DialogClose>
              <DialogClose asChild>
                <Button type="submit">Create Environment</Button>
              </DialogClose>
            </DialogFooter>
          }
        />
      </DialogContent>
    </Dialog>
  );
};
