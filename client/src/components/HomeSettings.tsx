import { SettingsLayout } from "@/components/SettingsLayout";
import { Typography } from "@/components/ui/typography";
import { userQueryOptions } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { SettingsIcon } from "lucide-react";

export const HomeSettings = () => {
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const userOrganization = user.user_organizations?.find(
    (userOrg) => userOrg.organization.uuid === user?.active_organization_uuid
  );
  return (
    <SettingsLayout title='Overview' icon={SettingsIcon}>
      <Typography variant='h4'>Personal Information</Typography>
      <div className='grid gap-4'>
        <div className='space-y-2'>
          <label className='text-sm font-medium text-gray-700'>Name</label>
          <div className='p-2 bg-gray-100 rounded-md text-gray-800'>
            {user.first_name}
          </div>
        </div>
        <div className='space-y-2'>
          <label className='text-sm font-medium text-gray-700'>Email</label>
          <div className='p-2 bg-gray-100 rounded-md text-gray-800'>
            {user.email}
          </div>
        </div>
        {userOrganization && (
          <div className='space-y-2'>
            <label className='text-sm font-medium text-gray-700'>
              Organization
            </label>
            <div className='p-2 bg-gray-100 rounded-md text-gray-800'>
              {userOrganization.organization.name}
            </div>
          </div>
        )}
      </div>
    </SettingsLayout>
  );
};
