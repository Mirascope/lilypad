import LilypadDialog from "@/components/LilypadDialog";
import { SettingsLayout } from "@/components/SettingsLayout";
import { Button } from "@/components/ui/button";
import { DialogClose, DialogFooter } from "@/components/ui/dialog";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
} from "@/components/ui/form";
import { Textarea } from "@/components/ui/textarea";
import { Typography } from "@/components/ui/typography";
import { Tier } from "@/ee/types/types";
import { isLilypadCloud } from "@/ee/utils/common";
import { licenseQueryOptions } from "@/ee/utils/organizations";
import { toast } from "@/hooks/use-toast";
import { OrganizationUpdate } from "@/types/types";
import { useUpdateOrganizationMutation } from "@/utils/organizations";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { SettingsIcon } from "lucide-react";
import { useForm } from "react-hook-form";

const tier = {
  [Tier.FREE]: "Free",
  [Tier.PRO]: "Pro",
  [Tier.TEAM]: "Team",
  [Tier.ENTERPRISE]: "Enterprise",
};
export const HomeSettings = () => {
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const { data: licenseInfo } = useSuspenseQuery(licenseQueryOptions());
  const userOrganization = user.user_organizations?.find(
    (userOrg) => userOrg.organization.uuid === user?.active_organization_uuid
  );
  return (
    <SettingsLayout title='Overview' icon={SettingsIcon}>
      <Typography variant='h4'>Personal Information</Typography>
      <div className='grid gap-4'>
        <UneditableInput label='Name' value={user.first_name} />
        <UneditableInput label='Email' value={user.email} />
        <Typography variant='h4'>Organization</Typography>
        {userOrganization && (
          <UneditableInput
            label='Name'
            value={userOrganization.organization.name}
          />
        )}
        <UneditableInput
          label='Plan'
          value={`${tier[licenseInfo.tier]} Plan`}
        />
        {!isLilypadCloud() && (
          <div>
            <LilypadDialog
              title='Change Plan'
              description='Contact william@mirascope.com to obtain a new license key.'
              buttonProps={{
                variant: "default",
              }}
              text={"Upgrade plan"}
            >
              <ChangePlan />
            </LilypadDialog>
          </div>
        )}
      </div>
    </SettingsLayout>
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
    try {
      await updateOrganization.mutateAsync(data);
      toast({
        title: "Successfully upgraded plan.",
      });
    } catch (e) {
      toast({
        title: "Failed to upgrade plan.",
        variant: "destructive",
      });
    }
  };
  return (
    <Form {...methods}>
      <form
        onSubmit={methods.handleSubmit(onSubmit)}
        className='flex flex-col gap-3'
      >
        <FormField
          key='licenseKey'
          control={methods.control}
          name='license'
          render={({ field }) => (
            <FormItem>
              <FormLabel>License</FormLabel>
              <FormControl>
                <Textarea {...field} value={field.value || ""} />
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
              {methods.formState.isSubmitting ? "Upgrading..." : "Upgrade Plan"}
            </Button>
          </DialogClose>
        </DialogFooter>
      </form>
    </Form>
  );
};
const UneditableInput = ({
  label,
  value,
}: {
  label: string;
  value: string;
}) => {
  return (
    <div className='space-y-2'>
      <label className='text-sm font-medium text-gray-700'>{label}</label>
      <div className='p-2 bg-gray-100 rounded-md text-gray-800'>{value}</div>
    </div>
  );
};
