import { Button } from "@/src/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/src/components/ui/dialog";
import { InviteUserForm } from "@/src/components/users/InviteUserForm";
import { cn } from "@/src/lib/utils";
import { PlusCircle } from "lucide-react";

interface InviteUserDialogProps {
  title: string;
  description?: string;
  maxWidth?: string;
}

export const InviteUserDialog = ({
  title,
  description,
  maxWidth = "[425px]",
}: InviteUserDialogProps) => {
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
      <DialogContent className={cn(`max-w-${maxWidth} overflow-x-auto`)}>
        <DialogHeader className="shrink-0">
          <DialogTitle>{title}</DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>
        <InviteUserForm />
      </DialogContent>
    </Dialog>
  );
};
