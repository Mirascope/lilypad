import { KeyRound, Eye, EyeOff } from "lucide-react";
import { useUpdateUserKeysMutation } from "@/utils/users";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { useAuth } from "@/auth";
import { useForm, useFormContext } from "react-hook-form";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { useState } from "react";
import { Typography } from "@/components/ui/typography";
import { SettingsLayout } from "@/components/SettingsLayout";

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

export const KeysSettings = () => {
  const { user, setSession } = useAuth();
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
      const userSession = await updateUserKeys.mutateAsync(data);
      setSession(userSession);
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
