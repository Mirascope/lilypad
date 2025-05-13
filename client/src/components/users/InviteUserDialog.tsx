import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { InviteUserForm } from "@/components/users/InviteUserForm";
import { cn } from "@/lib/utils";
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
          className="text-primary hover:text-primary/80 hover:bg-background"
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
