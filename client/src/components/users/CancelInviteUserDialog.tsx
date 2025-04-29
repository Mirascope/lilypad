import LilypadDialog from "@/components/LilypadDialog";
import { Button } from "@/components/ui/button";
import { OrganizationInvitePublic } from "@/types/types";
import { useDeleteOrganizationInviteMutation } from "@/utils/organizations";
import { Trash } from "lucide-react";
import { toast } from "sonner";

export const CancelInviteUserDialog = ({
  invite,
}: {
  invite: OrganizationInvitePublic & { isInvite: true };
}) => {
  const deleteInvite = useDeleteOrganizationInviteMutation();

  const handleDelete = () => {
    deleteInvite
      .mutateAsync(invite.uuid)
      .then(() => {
        toast.success("Invitation cancelled successfully");
      })
      .catch(() => {
        toast.error("Failed to cancel invitation");
      });
  };

  return (
    <LilypadDialog
      title='Remove invitation'
      description={`Are you sure you want to rescind the invitation to ${invite.email}?`}
      dialogContentProps={{
        onClick: (e) => e.stopPropagation(),
      }}
      customTrigger={
        <Button
          variant='outlineDestructive'
          size='icon'
          className='h-8 w-8'
          onClick={(e) => e.stopPropagation()}
        >
          <Trash size={16} />
        </Button>
      }
      dialogButtons={[
        <Button
          key='remove-invitation'
          variant='destructive'
          onClick={(e) => {
            e.stopPropagation();
            e.preventDefault();
            handleDelete();
          }}
        >
          Remove invitation
        </Button>,
        <Button variant='outline' key='remove-invitation-close'>
          Close
        </Button>,
      ]}
    />
  );
};
