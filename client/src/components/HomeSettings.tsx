import { SettingsLayout } from "@/components/SettingsLayout";
import { Typography } from "@/components/ui/typography";
import { licenseQueryOptions } from "@/ee/utils/organizations";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { capitalize } from "lodash";
import { SettingsIcon } from "lucide-react";

export const HomeSettings = () => {
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const { data: licenseInfo } = useSuspenseQuery(licenseQueryOptions());
  const userOrganization = user.user_organizations?.find(
    (userOrg) => userOrg.organization.uuid === user?.active_organization_uuid
  );
  console.log(licenseInfo);
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
        <UneditableInput label='License' value={capitalize(licenseInfo.tier)} />
      </div>
    </SettingsLayout>
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
