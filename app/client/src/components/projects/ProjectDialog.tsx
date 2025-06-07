import { ProjectFormData } from "@/src/components/projects/BaseProjectForm";
import { CreateProjectForm } from "@/src/components/projects/CreateProjectForm";
import { DeleteProjectForm } from "@/src/components/projects/DeleteProjectForm";
import { EditProjectForm } from "@/src/components/projects/EditProjectForm";
import { Button } from "@/src/components/ui/button";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/src/components/ui/dialog";
import { ProjectPublic } from "@/src/types/types";
import { PencilLine, PlusCircle, Trash } from "lucide-react";
import { ReactNode } from "react";
interface BaseDialogProps {
  trigger: ReactNode;
  title: string;
  description?: string;
  children: ReactNode;
  maxWidth?: string;
  closeOnSubmit?: boolean;
}

export const BaseProjectDialog = ({
  trigger,
  title,
  description,
  children,
  maxWidth = "md",
  closeOnSubmit = true,
}: BaseDialogProps) => {
  return (
    <Dialog>
      <DialogTrigger asChild onClick={(e) => e.stopPropagation()}>
        {trigger}
      </DialogTrigger>
      <DialogContent
        className={`max-w-${maxWidth} overflow-x-auto`}
        onClick={(e) => e.stopPropagation()}
      >
        <DialogHeader className="shrink-0">
          <DialogTitle>{title}</DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>

        {closeOnSubmit ? <DialogClose asChild>{children}</DialogClose> : children}
      </DialogContent>
    </Dialog>
  );
};

export const CreateProjectDialog = () => {
  return (
    <BaseProjectDialog
      trigger={
        <Button
          variant="ghost"
          size="iconSm"
          className="text-primary hover:bg-background hover:text-primary/80"
        >
          <PlusCircle />
        </Button>
      }
      title="Create a new project"
      description="Create a new project for your organization."
    >
      <CreateProjectForm />
    </BaseProjectDialog>
  );
};

export const EditProjectDialog = ({
  projectUuid,
  defaultProjectFormData,
}: {
  projectUuid: string;
  defaultProjectFormData: ProjectFormData;
}) => {
  return (
    <BaseProjectDialog
      trigger={
        <Button variant="outline" size="icon" className="h-8 w-8">
          <PencilLine />
        </Button>
      }
      title="Edit project"
      description="Update your project details."
    >
      <EditProjectForm projectUuid={projectUuid} defaultProjectFormData={defaultProjectFormData} />
    </BaseProjectDialog>
  );
};

export const DeleteProjectDialog = ({ project }: { project: ProjectPublic }) => {
  return (
    <BaseProjectDialog
      trigger={
        <Button variant="outlineDestructive" size="icon" className="h-8 w-8">
          <Trash />
        </Button>
      }
      title={`Delete ${project.name}`}
      description={`Deleting ${project.name} will delete all resources tied to this project.`}
      maxWidth="[425px]"
      closeOnSubmit={false}
    >
      <DeleteProjectForm project={project} />
    </BaseProjectDialog>
  );
};
