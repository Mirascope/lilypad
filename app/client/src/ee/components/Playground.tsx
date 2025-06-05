import { AddCardButton } from "@/src/components/AddCardButton";
import { NotFound } from "@/src/components/NotFound";
import { Button } from "@/src/components/ui/button";
import { Card, CardContent } from "@/src/components/ui/card";
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/src/components/ui/form";
import { Input } from "@/src/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/src/components/ui/select";
import {
  Sheet,
  SheetClose,
  SheetContent,
  SheetFooter,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/src/components/ui/sheet";
import { Tooltip, TooltipContent, TooltipTrigger } from "@/src/components/ui/tooltip";
import { Editor } from "@/src/ee/components/Editor";
import { EditorParameters, usePlaygroundContainer } from "@/src/ee/hooks/use-playground";
import { TypedInput } from "@/src/ee/utils/input-utils";
import { FunctionPublic, PlaygroundErrorDetail } from "@/src/types/types";
import { BaseEditorFormFields, validateInputs } from "@/src/utils/playground-utils";
import { X } from "lucide-react";
import { Dispatch, SetStateAction, useEffect } from "react";
import { SubmitHandler, useFieldArray, useFormContext } from "react-hook-form";

export const Playground = ({
  version,
  isCompare,
  showRunButton,
  playgroundContainer,
}: {
  version: FunctionPublic | null;
  error?: PlaygroundErrorDetail | null;
  isCompare?: boolean;
  showRunButton?: boolean;
  playgroundContainer?: ReturnType<typeof usePlaygroundContainer>;
}) => {
  const defaultContainer = usePlaygroundContainer({
    version,
  });

  const {
    methods,
    editorRef,
    inputs,
    inputValues,
    editorErrors,
    openInputDrawer,
    setOpenInputDrawer,
    doesProviderExist,
    isRunLoading,
    onSubmit,
    handleReset,
    projectUuid,
  } = playgroundContainer ?? defaultContainer;

  if (!projectUuid) return <NotFound />;

  const renderRunButton = () => {
    return (
      <Tooltip>
        <TooltipTrigger asChild>
          <span>
            <Button
              name="run"
              loading={isRunLoading}
              disabled={!doesProviderExist}
              className="font-medium text-white hover:bg-green-700"
            >
              Run
            </Button>
          </span>
        </TooltipTrigger>
        <TooltipContent className="bg-gray-700 text-white">
          <p className="max-w-xs break-words">
            {doesProviderExist ? (
              "Run the playground with the selected provider."
            ) : (
              <span>You need to add an API key to run the playground.</span>
            )}
          </p>
        </TooltipContent>
      </Tooltip>
    );
  };

  return (
    <Form {...methods}>
      <div className="h-full">
        <div className="flex h-full flex-col">
          <form
            id={`playground-form-${version?.uuid ?? Math.random().toString(36).substring(7)}`}
            onSubmit={methods.handleSubmit(onSubmit)}
            className="flex h-full flex-1 flex-col gap-4"
          >
            <div className="flex w-full justify-between gap-4">
              <div className="flex items-center gap-2">
                <InputsDrawer
                  open={openInputDrawer}
                  setOpen={setOpenInputDrawer}
                  onSubmit={onSubmit}
                  doesProviderExist={doesProviderExist}
                  isLoading={isRunLoading}
                  isDisabled={isRunLoading}
                />
                <CallParamsDrawer
                  doesProviderExist={doesProviderExist}
                  version={version}
                  isLoading={isRunLoading}
                  isDisabled={isRunLoading}
                  handleReset={handleReset}
                />
                {(!isCompare || showRunButton) && renderRunButton()}
              </div>
            </div>
            <div className="lexical relative min-h-[200px] flex-1">
              <Editor
                inputs={inputs.map((input) => input.key)}
                inputValues={inputValues}
                ref={editorRef}
                template={version?.prompt_template ?? ""}
                isDisabled={isRunLoading}
                isLLM={true}
              />
              {editorErrors.length > 0 &&
                editorErrors.map((error, i) => (
                  <div key={i} className="mt-1 text-sm text-red-500">
                    {error}
                  </div>
                ))}
            </div>
          </form>
        </div>
      </div>
    </Form>
  );
};

const CallParamsDrawer = ({
  doesProviderExist,
  isLoading,
  version,
  isDisabled,
  handleReset,
}: {
  doesProviderExist: boolean;
  isLoading: boolean;
  version: FunctionPublic | null;
  isDisabled: boolean;
  handleReset: () => void;
}) => {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button
          className="border border-gray-300 bg-background text-gray-700 hover:bg-gray-100"
          variant="outline"
          disabled={isDisabled}
        >
          Configure Call Params
        </Button>
      </SheetTrigger>
      <SheetContent className="flex flex-col gap-2 overflow-y-auto" showOverlay={false}>
        <SheetHeader>
          <SheetTitle>Call Params</SheetTitle>
        </SheetHeader>
        {!isDisabled && (
          <div className="self-end">
            <SheetClose asChild>
              <Button
                form={`playground-form-${version?.uuid ?? Math.random().toString(36).substring(7)}`}
                name="run"
                type="submit"
                loading={isLoading}
                disabled={!doesProviderExist}
                className="font-medium text-white hover:bg-green-700"
              >
                Run
              </Button>
            </SheetClose>
          </div>
        )}
        <BaseEditorFormFields isDisabled={isDisabled} />
        <SheetFooter>
          {!isDisabled && (
            <Button variant="outline" onClick={handleReset}>
              Reset to default
            </Button>
          )}
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
};

const InputsDrawer = ({
  open,
  setOpen,
  onSubmit,
  doesProviderExist,
  isLoading,
  isDisabled,
}: {
  open: boolean;
  setOpen: Dispatch<SetStateAction<boolean>>;
  onSubmit: SubmitHandler<EditorParameters>;
  doesProviderExist: boolean;
  isLoading: boolean;
  isDisabled: boolean;
}) => {
  const methods = useFormContext<EditorParameters>();
  const inputs = methods.watch("inputs");

  const handleClick = async (event: React.MouseEvent<HTMLButtonElement>) => {
    if (!validateInputs(methods, inputs)) {
      return;
    }
    await methods.handleSubmit((data) => onSubmit(data, event))();
  };

  useEffect(() => {
    if (isLoading && open) {
      setOpen(false);
    }
  }, [isLoading, open, setOpen]);

  return (
    <Sheet open={open} onOpenChange={setOpen}>
      <SheetTrigger asChild>
        <Button
          className="border border-gray-300 bg-background text-gray-700 hover:bg-gray-100"
          variant="outline"
          disabled={isDisabled}
        >
          Inputs
        </Button>
      </SheetTrigger>
      <SheetContent
        className="flex flex-col overflow-y-auto sm:max-w-xl md:max-w-2xl"
        showOverlay={false}
      >
        <SheetHeader>
          <SheetTitle>Inputs</SheetTitle>
        </SheetHeader>
        {!isDisabled && (
          <div className="self-end">
            <Button
              name="run"
              onClick={handleClick}
              loading={isLoading}
              disabled={!doesProviderExist}
              className="font-medium text-white hover:bg-green-700"
            >
              Run
            </Button>
          </div>
        )}
        <InputsContent isDisabled={isDisabled} />
        <SheetFooter>
          <SheetClose asChild>
            <Button variant="outline">Close</Button>
          </SheetClose>
        </SheetFooter>
      </SheetContent>
    </Sheet>
  );
};

const InputsContent = ({ isDisabled }: { isDisabled: boolean }) => {
  const methods = useFormContext<EditorParameters>();
  const { fields, append, remove } = useFieldArray<EditorParameters>({
    control: methods.control,
    name: "inputs",
  });
  const types = ["str", "int", "float", "bool", "bytes", "list", "dict"];

  return (
    <div className="space-y-2">
      <div className="flex flex-wrap gap-4 pb-4">
        {fields.map((field, index) => {
          const type = methods.watch(`inputs.${index}.type`);
          return (
            <Card key={field.id} className="relative w-full shrink-0">
              {!isDisabled && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={() => remove(index)}
                  className="absolute top-2 right-2 h-6 w-6 hover:bg-gray-100"
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
              <CardContent className="space-y-4 pt-6">
                <div className="w-full">
                  <FormField
                    control={methods.control}
                    name={`inputs.${index}.key`}
                    rules={{ required: "Argument name is required" }}
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Args</FormLabel>
                        <FormControl>
                          <Input placeholder="Argument Name" disabled={isDisabled} {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                </div>
                <div className="flex w-full gap-2">
                  <FormField
                    control={methods.control}
                    name={`inputs.${index}.type`}
                    rules={{ required: "Type is required" }}
                    render={({ field }) => (
                      <FormItem className="flex-1">
                        <FormLabel>Type</FormLabel>
                        <FormControl>
                          <Select
                            value={field.value}
                            onValueChange={field.onChange}
                            disabled={isDisabled}
                          >
                            <SelectTrigger className="w-full">
                              <SelectValue placeholder="Select input type" />
                            </SelectTrigger>
                            <SelectContent>
                              {types.map((type) => (
                                <SelectItem key={type} value={type}>
                                  {type}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <div className="flex-1">
                    <TypedInput<EditorParameters>
                      name={`inputs.${index}.value`}
                      type={type as any}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          );
        })}
        {!isDisabled && (
          <AddCardButton
            className="w-full"
            onClick={() => append({ key: "", type: "str", value: "" })}
          />
        )}
      </div>
    </div>
  );
};
