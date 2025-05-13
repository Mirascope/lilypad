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
import { Form } from "@/components/ui/form";
import { UserOrganizationPublic, UserPublic } from "@/types/types";
import { useDeleteUserOrganizationMutation } from "@/utils/users";
import { Trash } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

export const RemoveUserDialog = ({
  userOrganization,
  user,
}: {
  userOrganization: UserOrganizationPublic;
  user: UserPublic;
}) => {
  const methods = useForm();
  const deleteUserOrganization = useDeleteUserOrganizationMutation();
  const onSubmit = async () => {
    const successfullyDeleted = await deleteUserOrganization
      .mutateAsync(userOrganization.uuid)
      .catch(() => {
        toast.error("Failed to remove user. Please try again.");
      });
    if (successfullyDeleted) {
      toast.success("Successfully removed user from organization");
    }
  };

  return (
    <Dialog>
      <DialogTrigger asChild onClick={(e) => e.stopPropagation()}>
        <Button variant='outlineDestructive' size='icon' className='h-8 w-8'>
          <Trash />
        </Button>
      </DialogTrigger>
      <DialogContent
        className={"max-w-[425px] overflow-x-auto"}
        onClick={(e) => e.stopPropagation()}
      >
        <Form {...methods}>
          <form onSubmit={methods.handleSubmit(onSubmit)} className='space-y-6'>
            <DialogHeader className='shrink-0'>
              <DialogTitle>{`Remove ${user.first_name}`}</DialogTitle>
            </DialogHeader>
            <DialogDescription>
              This action will remove <b>{user.first_name}</b> from{" "}
              <b>{userOrganization.organization.name}</b>
            </DialogDescription>
            <DialogFooter>
              <DialogClose asChild>
                <Button
                  type='submit'
                  variant='destructive'
                  loading={methods.formState.isSubmitting}
                  className='w-full'
                >
                  {methods.formState.isSubmitting
                    ? "Removing..."
                    : "Remove user"}
                </Button>
              </DialogClose>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  );
};
