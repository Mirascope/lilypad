import { Button } from "@/components/ui/button";
import { DialogClose } from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { OrganizationInviteCreate, OrganizationInvitePublic } from "@/types/types";
import { useCreateOrganizationInviteMutation } from "@/utils/organizations";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Copy } from "lucide-react";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

export const AlternativeInviteLink = ({ inviteLink }: { inviteLink: string }) => {
  return (
    <>
      <div>Alternatively, give the invited user this link:</div>
      <div className="flex items-center space-x-2">
        <Input value={inviteLink} readOnly />
        <Button
          variant="outline"
          size="icon"
          type="button"
          onClick={(e) => {
            e.stopPropagation();
            navigator.clipboard.writeText(inviteLink).catch(() => {
              toast.error("Failed to copy link");
            });
            toast.success("Copied link to clipboard");
          }}
        >
          <Copy />
        </Button>
      </div>
    </>
  );
};

interface InviteUserFormProps {
  onSuccess?: (invite: OrganizationInvitePublic) => void;
  className?: string;
}

export const InviteUserForm = ({ onSuccess, className = "" }: InviteUserFormProps) => {
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const methods = useForm<OrganizationInviteCreate>({
    defaultValues: { email: "", invited_by: user.uuid },
  });
  const [organizationInvite, setOrganizationInvite] = useState<OrganizationInvitePublic | null>(
    null
  );

  const createOrganizationInvite = useCreateOrganizationInviteMutation();

  const handleSubmit = async (data: OrganizationInviteCreate) => {
    const created = await createOrganizationInvite.mutateAsync(data);
    setOrganizationInvite(created);

    if (created.resend_email_id !== "n/a") {
      toast.success(`Successfully sent email invite to ${data.email}.`);
    }

    onSuccess?.(created);
  };

  return (
    <Form {...methods}>
      <form onSubmit={methods.handleSubmit(handleSubmit)} className={`space-y-6 ${className}`}>
        <FormField
          key="email"
          control={methods.control}
          name="email"
          rules={{
            required: "Email is required",
            pattern: {
              value: /\S+@\S+\.\S+/,
              message: "Invalid email",
            },
          }}
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input {...field} />
              </FormControl>
              <FormDescription />
            </FormItem>
          )}
        />

        {organizationInvite?.invite_link && (
          <AlternativeInviteLink inviteLink={organizationInvite.invite_link} />
        )}

        <div className="flex justify-end">
          {!organizationInvite ? (
            <Button type="submit" disabled={methods.formState.isSubmitting}>
              {methods.formState.isSubmitting ? "Sending invite..." : "Send invite"}
            </Button>
          ) : (
            <DialogClose asChild>
              <Button type="button" variant="outline" onClick={() => setOrganizationInvite(null)}>
                Close
              </Button>
            </DialogClose>
          )}
        </div>
      </form>
    </Form>
  );
};
