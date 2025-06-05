import { Button } from "@/src/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/src/components/ui/dialog";
import { AlternativeInviteLink } from "@/src/components/users/InviteUserForm";
import { OrganizationInvitePublic } from "@/src/types/types";
import { useCreateOrganizationInviteMutation } from "@/src/utils/organizations";
import { Dispatch, SetStateAction, useState } from "react";
import { toast } from "sonner";
export const ResendInviteUserDialog = ({
  invite,
  open,
  setOpen,
  onClose,
}: {
  invite: OrganizationInvitePublic & { isInvite: true };
  open: boolean;
  setOpen: Dispatch<SetStateAction<boolean>>;
  onClose: () => void;
}) => {
  const resendInvite = useCreateOrganizationInviteMutation();
  const [newOrganizationInvite, setNewOrganizationInvite] =
    useState<OrganizationInvitePublic | null>(null);

  const handleClose = () => {
    setOpen(false);
    setNewOrganizationInvite(null);
    onClose();
  };

  const handleResend = async () => {
    const result = await resendInvite
      .mutateAsync({
        email: invite.email,
        organization_uuid: invite.organization_uuid,
        invited_by: invite.invited_by,
      })
      .catch(() => {
        toast.error("Failed to resend invitation");
        return null;
      });
    if (!result) {
      return;
    }
    setNewOrganizationInvite(result);
    toast.success(`Invitation successfully resent to ${invite.email}.`);
  };

  return (
    <Dialog
      open={open}
      onOpenChange={(newOpen) => {
        if (!newOpen) {
          handleClose();
        } else {
          setOpen(true);
        }
      }}
    >
      <DialogContent onClick={(e) => e.stopPropagation()}>
        <DialogHeader>
          <DialogTitle>Resend invitation</DialogTitle>
          <DialogDescription>
            {!newOrganizationInvite
              ? `Are you sure you want to resend the invitation to ${invite.email}?`
              : `Invitation successfully resent to ${invite.email}.`}
          </DialogDescription>
        </DialogHeader>

        {newOrganizationInvite?.invite_link && (
          <AlternativeInviteLink inviteLink={newOrganizationInvite.invite_link} />
        )}

        <DialogFooter>
          {!newOrganizationInvite ? (
            <Button
              loading={resendInvite.isPending}
              onClick={(e) => {
                e.stopPropagation();
                e.preventDefault();
                handleResend();
              }}
            >
              Resend invitation
            </Button>
          ) : (
            <Button onClick={handleClose}>Close</Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};
