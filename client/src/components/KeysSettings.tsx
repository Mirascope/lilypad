import { NotFound } from "@/components/NotFound";
import { SettingsLayout } from "@/components/SettingsLayout";
import { Button } from "@/components/ui/button";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form";
import { Input } from "@/components/ui/input";
import { Typography } from "@/components/ui/typography";
import { useToast } from "@/hooks/use-toast";
import {
  externalApiKeysQueryOptions,
  useCreateExternalApiKeyMutation,
  usePatchExternalApiKeyMutation,
} from "@/utils/external-api-keys";
import { userQueryOptions, useUpdateUserKeysMutation } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Eye, EyeOff, KeyRound } from "lucide-react";
import { useState } from "react";
import { useForm, useFormContext } from "react-hook-form";

interface UserKeysFormValues {
  openai: string;
  anthropic: string;
  gemini: string;
  openrouter: string;
}
interface KeyInput {
  id: keyof UserKeysFormValues;
  label: string;
}
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
  const { data: user } = useSuspenseQuery(userQueryOptions());
  const { data: externalApiKeys } = useSuspenseQuery(
    externalApiKeysQueryOptions()
  );
  const { toast } = useToast();
  const externalApiKeysMap = externalApiKeys.reduce(
    (acc, key) => {
      acc[key.service_name] = key.masked_api_key;
      return acc;
    },
    {} as Record<string, string>
  );
  const patchExternalApiKeys = usePatchExternalApiKeyMutation();
  const createExternalApiKeys = useCreateExternalApiKeyMutation();
  const updateUserKeys = useUpdateUserKeysMutation();
  const keys = user.keys ?? {};
  const methods = useForm<UserKeysFormValues>({
    defaultValues: {
      openai: externalApiKeysMap.openai ?? "",
      anthropic: externalApiKeysMap.anthropic ?? "",
      gemini: externalApiKeysMap.gemini ?? "",
      openrouter: externalApiKeysMap.openrouter || "",
    },
  });

  const onSubmit = async (data: UserKeysFormValues) => {
    try {
      for (const key in data) {
        if (data[key as keyof UserKeysFormValues] !== keys[key]) {
          if (externalApiKeysMap[key]) {
            await patchExternalApiKeys.mutateAsync({
              serviceName: key as keyof UserKeysFormValues,
              externalApiKeysUpdate: {
                api_key: data[key as keyof UserKeysFormValues],
              },
            });
          } else {
            await createExternalApiKeys.mutateAsync({
              service_name: key as keyof UserKeysFormValues,
              api_key: data[key as keyof UserKeysFormValues],
            });
          }
        }
      }
      await updateUserKeys.mutateAsync(data);
      toast({
        title: "LLM Keys Updated",
        description: "Your LLM API keys have been updated.",
      });
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
  if (!user) return <NotFound />;
  return (
    <SettingsLayout title={`${user.first_name}'s Keys`} icon={KeyRound}>
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
