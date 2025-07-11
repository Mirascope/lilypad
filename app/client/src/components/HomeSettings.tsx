import { isLilypadCloud } from "@/src/ee/utils/common";
import { licenseQueryOptions } from "@/src/ee/utils/organizations";
import { FontToggle } from "@/src/components/FontToggle";
import LilypadDialog from "@/src/components/LilypadDialog";
import { ModeToggle } from "@/src/components/mode-toggle";
import { CreateOrganizationDialog } from "@/src/components/OrganizationDialog";
import { Button } from "@/src/components/ui/button";
import { DialogClose, DialogFooter } from "@/src/components/ui/dialog";
import { Form, FormControl, FormField, FormItem, FormLabel } from "@/src/components/ui/form";
import { Textarea } from "@/src/components/ui/textarea";
import { Typography } from "@/src/components/ui/typography";
import { OrganizationUpdate, Tier } from "@/src/types/types";
import { useUpdateOrganizationMutation } from "@/src/utils/organizations";
import { userQueryOptions } from "@/src/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { toast } from "sonner";

const tier = {
  [Tier.FREE]: "Free",
  [Tier.PRO]: "Pro",
  [Tier.TEAM]: "Team",
  [Tier.ENTERPRISE]: "Enterprise",
};
export const HomeSettings = () => {
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const userOrganization = user.user_organizations?.find(
    (userOrg) => userOrg.organization.uuid === user?.active_organization_uuid
  );
  const { data: licenseInfo } = useSuspenseQuery(licenseQueryOptions());
  const [open, setOpen] = useState<boolean>(false);
  return (
    <>
      <Typography variant="h3">Profile</Typography>
      <div className="flex flex-col gap-6">
        <div>
          <Typography variant="h5">Personal Information</Typography>
          <div className="grid gap-4">
            <UneditableInput label="Name" value={user.first_name} />
            <UneditableInput label="Email" value={user.email} />
          </div>
          <div className="my-2 flex flex-col">
            <label className="text-sm font-medium text-muted-foreground">Theme</label>
            <ModeToggle />
          </div>
          <div className="my-2 flex flex-col">
            <label className="text-sm font-medium text-muted-foreground">Font</label>
            <FontToggle />
          </div>
        </div>
        <div>
          <Typography variant="h5">Organization</Typography>
          <div className="grid gap-4">
            {userOrganization ? (
              <>
                <UneditableInput label="Name" value={userOrganization.organization.name} />
                <UneditableInput
                  label="Plan"
                  value={`${isLilypadCloud() ? "Cloud" : "Self-Host"} ${tier[licenseInfo.tier]} Plan`}
                />
                {!isLilypadCloud() && (
                  <div>
                    <LilypadDialog
                      title="Change Plan"
                      description="Contact william@mirascope.com to obtain a new license key."
                      buttonProps={{
                        variant: "default",
                      }}
                      text={"Upgrade plan"}
                    >
                      <ChangePlan />
                    </LilypadDialog>
                  </div>
                )}
              </>
            ) : (
              <Button onClick={() => setOpen(true)}>Create Organization</Button>
            )}
          </div>
        </div>
        <CreateOrganizationDialog open={open} setOpen={setOpen} />
      </div>
    </>
  );
};

const ChangePlan = () => {
  const methods = useForm<OrganizationUpdate>({
    defaultValues: {
      license: "",
    },
  });
  const updateOrganization = useUpdateOrganizationMutation();
  const onSubmit = async (data: OrganizationUpdate) => {
    await updateOrganization.mutateAsync(data).catch(() => toast.error("Failed to upgrade plan."));
    toast.success("Successfully upgraded plan.");
  };
  return (
    <Form {...methods}>
      <form onSubmit={methods.handleSubmit(onSubmit)} className="flex flex-col gap-3">
        <FormField
          key="licenseKey"
          control={methods.control}
          name="license"
          render={({ field }) => (
            <FormItem>
              <FormLabel>License</FormLabel>
              <FormControl>
                <Textarea {...field} value={field.value ?? ""} />
              </FormControl>
            </FormItem>
          )}
        />
        <DialogFooter>
          <DialogClose asChild>
            <Button type="submit" loading={methods.formState.isSubmitting} className="w-full">
              {methods.formState.isSubmitting ? "Upgrading..." : "Upgrade Plan"}
            </Button>
          </DialogClose>
        </DialogFooter>
      </form>
    </Form>
  );
};
const UneditableInput = ({ label, value }: { label: string; value: string }) => {
  return (
    <div className="space-y-2">
      <label className="text-sm font-medium text-muted-foreground">{label}</label>
      <div className="rounded-md bg-muted p-2 text-muted-foreground">{value}</div>
    </div>
  );
};
