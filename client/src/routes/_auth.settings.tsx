import { SettingsIcon, KeyRound, LucideIcon, Eye, EyeOff } from "lucide-react";
import { createFileRoute } from "@tanstack/react-router";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { useAuth } from "@/auth";
import { Typography } from "@/components/ui/typography";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useForm, useFormContext } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { useUpdateUserKeysMutation } from "@/utils/users";

export const Route = createFileRoute("/_auth/settings")({
  component: () => <Settings />,
});
type Tab = {
  label: string;
  value: string;
  component?: JSX.Element | null;
};
const Settings = () => {
  const tabs: Tab[] = [
    {
      label: "Overview",
      value: "overview",
      component: <HomeSettings />,
    },
    {
      label: "Keys",
      value: "keys",
      component: <KeysSettings />,
    },
  ];
  const tabWidth = 80 * tabs.length;
  return (
    <Tabs defaultValue='overview' className='flex flex-col h-full'>
      <div className='flex justify-center w-full'>
        <TabsList className={`w-[${tabWidth}px]`}>
          {tabs.map((tab) => (
            <TabsTrigger key={tab.value} value={tab.value}>
              {tab.label}
            </TabsTrigger>
          ))}
        </TabsList>
      </div>
      {tabs.map((tab) => (
        <TabsContent
          key={tab.value}
          value={tab.value}
          className='w-full bg-gray-50 h-full'
        >
          {tab.component}
        </TabsContent>
      ))}
    </Tabs>
  );
};
interface UserKeysFormValues {
  openai: string;
  anthropic: string;
  gemini: string;
  openrouter: string;
}
type KeyInput = {
  id: keyof UserKeysFormValues;
  label: string;
};
const SettingsLayout = ({
  children,
  icon: Icon = SettingsIcon,
  title,
}: {
  children: React.ReactNode;
  icon?: LucideIcon;
  title?: string;
}) => {
  return (
    <div className='min-h-screen bg-gray-50 p-8'>
      <div className='max-w-4xl mx-auto'>
        <Card>
          <CardHeader className='flex flex-row justify-center items-center gap-2'>
            <Icon className='w-8 h-8 text-gray-700' />
            <h2 className='text-2xl font-semibold'>{title}</h2>
          </CardHeader>
          <CardContent className='p-6'>{children}</CardContent>
        </Card>
      </div>
    </div>
  );
};

const PasswordField = ({ input }: { input: KeyInput }) => {
  const [isView, setIsView] = useState(false);
  const { control } = useFormContext<UserKeysFormValues>();

  return (
    <FormField
      control={control}
      name={input.id}
      render={({ field }) => (
        <FormItem>
          <FormLabel>{input.label}</FormLabel>
          <FormControl>
            <div className='relative'>
              <Input
                type={isView ? "text" : "password"}
                id={input.id}
                {...field}
                value={field.value}
                onChange={field.onChange}
              />
              {isView ? (
                <Eye
                  className='absolute right-2 top-2 z-10 cursor-pointer text-gray-500'
                  onClick={() => {
                    setIsView(!isView);
                  }}
                />
              ) : (
                <EyeOff
                  className='absolute right-2 top-2 z-10 cursor-pointer text-gray-500'
                  onClick={() => setIsView(!isView)}
                />
              )}
            </div>
          </FormControl>
          <FormMessage />
        </FormItem>
      )}
    />
  );
};

const KeysSettings = () => {
  const { user } = useAuth();
  const updateUserKeys = useUpdateUserKeysMutation();
  const keys = user?.keys || {};
  const methods = useForm<UserKeysFormValues>({
    defaultValues: {
      openai: keys["openai"] || "",
      anthropic: keys["anthropic"] || "",
      gemini: keys["gemini"] || "",
      openrouter: keys["openrouter"] || "",
    },
  });

  const onSubmit = async (data: UserKeysFormValues) => {
    try {
      updateUserKeys.mutateAsync(data);
    } catch (error) {
      console.error(error);
    }
  };

  const inputs: KeyInput[] = [
    { id: "openai", label: "OpenAI" },
    { id: "anthropic", label: "Anthropic" },
    { id: "gemini", label: "Gemini" },
    { id: "openrouter", label: "OpenRouter" },
  ];
  return (
    <SettingsLayout title='Keys' icon={KeyRound}>
      <Typography variant='h4'>API Keys</Typography>
      <Form {...methods}>
        <form onSubmit={methods.handleSubmit(onSubmit)} className='space-y-6'>
          <div className='space-y-4'>
            {inputs.map((input) => (
              <PasswordField key={input.id} input={input} />
            ))}
          </div>
          <Button
            type='submit'
            loading={methods.formState.isSubmitting}
            className='w-full'
          >
            {methods.formState.isSubmitting ? "Saving..." : "Save Keys"}
          </Button>
        </form>
      </Form>
    </SettingsLayout>
  );
};

const HomeSettings = () => {
  const { user } = useAuth();
  const userOrganization = user?.user_organizations?.find(
    (userOrg) => userOrg.organization.uuid === user?.active_organization_uuid
  );
  return (
    <SettingsLayout title='Overview' icon={SettingsIcon}>
      <Typography variant='h4'>Personal Information</Typography>
      <div className='grid gap-4'>
        <div className='space-y-2'>
          <label className='text-sm font-medium text-gray-700'>Name</label>
          <div className='p-2 bg-gray-100 rounded-md text-gray-800'>
            {user?.first_name}
          </div>
        </div>
        <div className='space-y-2'>
          <label className='text-sm font-medium text-gray-700'>Email</label>
          <div className='p-2 bg-gray-100 rounded-md text-gray-800'>
            {user?.email}
          </div>
        </div>
        {userOrganization && (
          <div className='space-y-2'>
            <label className='text-sm font-medium text-gray-700'>
              Organization
            </label>
            <div className='p-2 bg-gray-100 rounded-md text-gray-800'>
              {userOrganization?.organization.name}
            </div>
          </div>
        )}
      </div>
    </SettingsLayout>
  );
};
