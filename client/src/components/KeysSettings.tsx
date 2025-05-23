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
import {
  externalApiKeysQueryOptions,
  useCreateExternalApiKeyMutation,
  useDeleteExternalApiKeyMutation,
  usePatchExternalApiKeyMutation,
} from "@/utils/external-api-keys";
import { useUpdateUserKeysMutation } from "@/utils/users";
import { useSuspenseQuery } from "@tanstack/react-query";
import { Eye, EyeOff } from "lucide-react";
import { useState } from "react";
import { useForm, useFormContext } from "react-hook-form";
import { toast } from "sonner";

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
            <div className="relative">
              <Input type={isView ? "text" : "password"} id={input.id} {...field} />
              {isView ? (
                <Eye
                  className="absolute top-2 right-2 z-10 cursor-pointer text-gray-500"
                  onClick={() => {
                    setIsView(!isView);
                  }}
                />
              ) : (
                <EyeOff
                  className="absolute top-2 right-2 z-10 cursor-pointer text-gray-500"
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
  const { data: externalApiKeys } = useSuspenseQuery(externalApiKeysQueryOptions());
  const externalApiKeysMap = externalApiKeys.reduce(
    (acc, key) => {
      acc[key.service_name] = key.masked_api_key;
      return acc;
    },
    {} as Record<string, string>
  );
  const patchExternalApiKeys = usePatchExternalApiKeyMutation();
  const createExternalApiKeys = useCreateExternalApiKeyMutation();
  const deleteExternalApiKeys = useDeleteExternalApiKeyMutation();
  const updateUserKeys = useUpdateUserKeysMutation();

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
      // Get dirty fields to process only the ones modified by the user
      const { dirtyFields } = methods.formState;
      const promises: Promise<any>[] = []; // Array to hold promises for parallel execution

      for (const key of Object.keys(data) as Array<keyof UserKeysFormValues>) {
        if (dirtyFields[key]) {
          const newValue = data[key].trim();
          const existsInExternal = externalApiKeysMap[key];

          if (existsInExternal) {
            if (newValue.length === 0) {
              promises.push(deleteExternalApiKeys.mutateAsync(key));
            } else {
              promises.push(
                patchExternalApiKeys.mutateAsync({
                  serviceName: key,
                  externalApiKeysUpdate: {
                    api_key: newValue,
                  },
                })
              );
            }
          } else if (newValue.length > 0) {
            promises.push(
              createExternalApiKeys.mutateAsync({
                service_name: key,
                api_key: newValue,
              })
            );
          }
        }
      }

      await Promise.all(promises);

      // Only call updateUserKeys if any field was actually changed.
      // This might be necessary if user.keys needs to be synced or for other side effects.
      if (Object.keys(dirtyFields).length > 0) {
        await updateUserKeys.mutateAsync(data); // Pass the full data as original logic did
      }
      toast.success("Your keys have been successfully updated.");
    } catch (error) {
      toast.error("Failed to update keys. Please try again.");
    }
  };

  const inputs: KeyInput[] = [
    { id: "openai", label: "OpenAI" },
    { id: "anthropic", label: "Anthropic" },
    { id: "gemini", label: "Gemini" },
    { id: "openrouter", label: "OpenRouter" },
  ];
  return (
    <>
      <Typography variant="h4">API Keys</Typography>
      <Form {...methods}>
        <form onSubmit={methods.handleSubmit(onSubmit)} className="space-y-6">
          <div className="space-y-4">
            {inputs.map((input) => (
              <PasswordField key={input.id} input={input} />
            ))}
          </div>
          <Button
            type="submit"
            // Use mutation pending states for more accurate loading indication
            loading={
              patchExternalApiKeys.isPending ||
              createExternalApiKeys.isPending ||
              deleteExternalApiKeys.isPending ||
              updateUserKeys.isPending
            }
            disabled={
              patchExternalApiKeys.isPending ||
              createExternalApiKeys.isPending ||
              deleteExternalApiKeys.isPending ||
              updateUserKeys.isPending
            }
            className="w-full"
          >
            {patchExternalApiKeys.isPending ||
            createExternalApiKeys.isPending ||
            deleteExternalApiKeys.isPending ||
            updateUserKeys.isPending
              ? "Saving..."
              : "Save Keys"}
          </Button>
        </form>
      </Form>
    </>
  );
};
