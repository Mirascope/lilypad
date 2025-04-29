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
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  UserOrganizationPublic,
  UserOrganizationUpdate,
  UserPublic,
  UserRole,
} from "@/types/types";
import { useUpdateUserOrganizationMutation } from "@/utils/users";
import { PencilLine } from "lucide-react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

export const EditUserPermissionsDialog = ({
  userOrganization,
  user,
}: {
  userOrganization: UserOrganizationPublic;
  user: UserPublic;
}) => {
  const updateUserOrganization = useUpdateUserOrganizationMutation();
  const methods = useForm<UserOrganizationUpdate>({
    defaultValues: { role: userOrganization?.role },
  });
  const onSubmit = async (data: UserOrganizationUpdate) => {
    await updateUserOrganization
      .mutateAsync({
        userOrganizationUuid: userOrganization.uuid,
        data,
      })
      .catch(() => {
        toast.error("Failed to update user permissions");
      });
    toast.success("Successfully updated user permissions");
  };
  const roles = Object.values(UserRole).filter(
    (role) => role !== UserRole.OWNER
  );
  return (
    <div onClick={(e) => e.stopPropagation()}>
      <Dialog>
        <DialogTrigger asChild>
          <Button variant='outline' size='icon' className='h-8 w-8'>
            <PencilLine />
          </Button>
        </DialogTrigger>
        <DialogContent className='max-w-[425px] overflow-x-auto'>
          <Form {...methods}>
            <form
              onSubmit={methods.handleSubmit(onSubmit)}
              className='space-y-6'
            >
              <DialogHeader className='flex-shrink-0'>
                <DialogTitle>{`Edit permissions for ${user.first_name}`}</DialogTitle>
              </DialogHeader>
              <DialogDescription>
                Update <b>{user.first_name}'s</b> role within the organization.
              </DialogDescription>
              <FormField
                key='role'
                control={methods.control}
                name='role'
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Role</FormLabel>
                    <FormControl>
                      <Select
                        value={field.value}
                        onValueChange={field.onChange}
                      >
                        <SelectTrigger className='w-full'>
                          <SelectValue placeholder='Change role' />
                        </SelectTrigger>
                        <SelectContent>
                          {roles.map((role) => (
                            <SelectItem key={role} value={role}>
                              {role}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </FormControl>
                  </FormItem>
                )}
              />
              <DialogFooter>
                <DialogClose asChild>
                  <Button
                    type='submit'
                    loading={methods.formState.isSubmitting}
                    className='w-full'
                  >
                    {methods.formState.isSubmitting ? "Updating..." : "Update"}
                  </Button>
                </DialogClose>
              </DialogFooter>
            </form>
          </Form>
        </DialogContent>
      </Dialog>
    </div>
  );
};
